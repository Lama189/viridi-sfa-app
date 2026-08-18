import asyncio
import json
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    WebAppInfo,
)
from aiohttp import ClientError, ClientSession, ClientTimeout


class Registration(StatesGroup):
    invite_code = State()
    phone = State()
    full_name = State()
    invite_code_existing = State()


def get_required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be configured")
    return value


def normalize_phone(phone: str) -> str | None:
    digits = "".join(character for character in phone if character.isdigit())
    if len(digits) == 9:
        digits = f"998{digits}"

    if len(digits) != 12 or not digits.startswith("998"):
        return None

    return f"+{digits}"


def market_keyboard(web_app_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть Viridi market",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ]
        ]
    )


def extract_error(response_text: str) -> str:
    try:
        detail = json.loads(response_text).get("detail")
    except (TypeError, ValueError):
        detail = None

    if isinstance(detail, str):
        return detail

    return "Не удалось завершить операцию. Проверьте код и попробуйте снова."


def create_router(api_url: str, web_app_url: str) -> Router:
    router = Router()
    normalized_api_url = api_url.rstrip("/")

    @router.message(CommandStart())
    async def start_registration(message: Message, state: FSMContext) -> None:
        if message.from_user is not None:
            telegram_chat_id = message.from_user.id
            try:
                async with (
                    ClientSession(timeout=ClientTimeout(total=10)) as client,
                    client.get(
                        f"{normalized_api_url}/api/v1/clients/by-telegram/{telegram_chat_id}"
                    ) as response,
                ):
                    if response.status == 200:
                        client_data = await response.json()
                        if client_data.get("has_retail_point"):
                            await state.clear()
                            await message.answer(
                                "С возвращением в Viridi market!\nНажмите кнопку ниже, чтобы открыть магазин.",
                                reply_markup=market_keyboard(web_app_url),
                            )
                            return

                        await state.set_state(Registration.invite_code_existing)
                        client_name = client_data.get("full_name") or "клиент"
                        await message.answer(
                            f"С возвращением, {client_name}!\n\n"
                            "Вы не привязаны ни к одной торговой точке.\n"
                            "Отправьте код активации новой торговой точки, чтобы продолжить.",
                            reply_markup=ReplyKeyboardRemove(),
                        )
                        return
            except ClientError:
                pass

        await state.set_state(Registration.invite_code)
        await message.answer(
            "Добро пожаловать в Viridi market.\n\nОтправьте код активации, чтобы зарегистрироваться.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @router.message(Registration.invite_code_existing, F.text)
    async def save_existing_invite_code(message: Message, state: FSMContext) -> None:
        if not message.text or message.from_user is None:
            return

        invite_code = message.text.strip()
        if not invite_code:
            await message.answer(
                "Код не должен быть пустым. Отправьте код активации ещё раз."
            )
            return

        payload = {
            "invite_code": invite_code,
            "telegram_chat_id": message.from_user.id,
        }

        try:
            async with (
                ClientSession(timeout=ClientTimeout(total=20)) as client,
                client.post(
                    f"{normalized_api_url}/api/v1/clients/join-by-invite",
                    json=payload,
                ) as response,
            ):
                response_text = await response.text()
                is_success = response.ok
        except ClientError:
            await message.answer(
                "Сервис временно недоступен. Попробуйте ещё раз позже."
            )
            return

        if is_success:
            await state.clear()
            await message.answer(
                "Вы успешно подключились к торговой точке! Добро пожаловать в Viridi market.",
                reply_markup=market_keyboard(web_app_url),
            )
            return

        await message.answer(extract_error(response_text))

    @router.message(Registration.invite_code, F.text)
    async def save_invite_code(message: Message, state: FSMContext) -> None:
        if not message.text:
            return

        invite_code = message.text.strip()
        if not invite_code:
            await message.answer(
                "Код не должен быть пустым. Отправьте код активации ещё раз."
            )
            return

        await state.update_data(invite_code=invite_code)
        await state.set_state(Registration.phone)
        await message.answer(
            "Теперь поделитесь номером телефона. Он нужен для оформления заказов.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Поделиться номером", request_contact=True)]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    @router.message(Registration.phone, F.contact)
    async def save_phone(message: Message, state: FSMContext) -> None:
        contact = message.contact
        if (
            contact is None
            or message.from_user is None
            or contact.user_id != message.from_user.id
        ):
            await message.answer(
                "Нажмите кнопку «Поделиться номером», чтобы отправить свой номер."
            )
            return

        phone = normalize_phone(contact.phone_number)
        if phone is None:
            await message.answer(
                "Нужен узбекский номер в формате +998XXXXXXXXX. Отправьте контакт ещё раз."
            )
            return

        await state.update_data(phone=phone)
        await state.set_state(Registration.full_name)
        await message.answer(
            "Как к вам обращаться? Отправьте имя и фамилию.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @router.message(Registration.phone)
    async def request_phone_contact(message: Message) -> None:
        await message.answer(
            "Нажмите кнопку «Поделиться номером», чтобы отправить свой номер."
        )

    @router.message(Registration.full_name, F.text)
    async def register_client(message: Message, state: FSMContext) -> None:
        if message.from_user is None or message.text is None:
            return

        full_name = message.text.strip()
        if not full_name:
            await message.answer("Имя не должно быть пустым. Отправьте имя и фамилию.")
            return

        registration_data = await state.get_data()
        payload = {
            "invite_code": registration_data["invite_code"],
            "phone": registration_data["phone"],
            "full_name": full_name,
            "telegram_chat_id": message.from_user.id,
        }

        try:
            async with (
                ClientSession(timeout=ClientTimeout(total=20)) as client,
                client.post(
                    f"{normalized_api_url}/api/v1/clients/register",
                    json=payload,
                ) as response,
            ):
                response_text = await response.text()
                is_success = response.ok
        except ClientError:
            await message.answer(
                "Сервис временно недоступен. Попробуйте ещё раз позже."
            )
            return

        if is_success:
            await state.clear()
            await message.answer(
                "Регистрация завершена. Добро пожаловать в Viridi market!",
                reply_markup=market_keyboard(web_app_url),
            )
            return

        if "already exists" in response_text.lower():
            await state.clear()
            await message.answer(
                "Вы уже зарегистрированы. Открывайте Viridi market.",
                reply_markup=market_keyboard(web_app_url),
            )
            return

        await message.answer(extract_error(response_text))

    @router.message(Registration.full_name)
    async def request_full_name(message: Message) -> None:
        await message.answer("Отправьте имя и фамилию текстом.")

    return router


async def main() -> None:
    token = get_required_env("TELEGRAM_BOT_TOKEN")
    api_url = get_required_env("VIRIDI_API_URL")
    web_app_url = get_required_env("TELEGRAM_WEB_APP_URL")

    bot = Bot(token=token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(create_router(api_url, web_app_url))

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    from telegram_bot.runner import main as runner_main

    asyncio.run(runner_main())
