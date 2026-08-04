import asyncio
import os
import aio_pika
from aio_pika import ExchangeType
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from telegram_bot.bot import create_router, get_required_env
from telegram_bot.consumers.order_events import OrderEventsConsumer
from telegram_bot.services.clients import ClientsService
from telegram_bot.services.notifications import NotificationService
from telegram_bot.services.retail_point_members import RetailPointMembersService


async def start_telegram_consumer(
    bot: Bot, api_url: str
) -> tuple[aio_pika.abc.AbstractRobustConnection, aio_pika.abc.AbstractChannel]:
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:123@localhost:5672/")

    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        "orders",
        ExchangeType.TOPIC,
        durable=True,
    )

    queue = await channel.declare_queue(
        "telegram.notifications",
        durable=True,
    )

    await queue.bind(
        exchange,
        routing_key="order.*",
    )

    retail_point_members = RetailPointMembersService(api_url)
    clients = ClientsService(api_url)

    notification_service = NotificationService(
        bot=bot,
        retail_point_members=retail_point_members,
        clients=clients,
    )

    consumer = OrderEventsConsumer(
        notification_service=notification_service,
    )

    await queue.consume(consumer.handle)
    return connection, channel


async def main() -> None:
    token = get_required_env("TELEGRAM_BOT_TOKEN")
    api_url = get_required_env("VIRIDI_API_URL")
    web_app_url = get_required_env("TELEGRAM_WEB_APP_URL")

    bot = Bot(token=token)
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.include_router(create_router(api_url, web_app_url))

    connection = None
    try:
        connection, _ = await start_telegram_consumer(bot, api_url)
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)
    finally:
        if connection and not connection.is_closed:
            await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
