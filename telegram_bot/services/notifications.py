from uuid import UUID

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.core.observability.logging import logger
from telegram_bot.events.order_events import (
    OrderAssemblyStartedEvent,
    OrderCreatedEvent,
)
from telegram_bot.services.clients import ClientsService
from telegram_bot.services.retail_point_members import RetailPointMembersService


class NotificationService:
    def __init__(
        self,
        bot: Bot,
        retail_point_members: RetailPointMembersService,
        clients: ClientsService,
    ) -> None:
        self._bot = bot
        self._retail_point_members = retail_point_members
        self._clients = clients

    async def order_created(
        self,
        event: OrderCreatedEvent | dict,
    ) -> None:
        if isinstance(event, dict):
            order_id = event["order_id"]
            retail_point_id_val = event["retail_point_id"]
            retail_point_id = (
                UUID(retail_point_id_val)
                if isinstance(retail_point_id_val, str)
                else retail_point_id_val
            )
        else:
            order_id = event.order_id
            retail_point_id = event.retail_point_id

        members = await self._retail_point_members.list_members(retail_point_id)

        for member in members:
            client = await self._clients.get(member.client_id)

            if client is None or client.telegram_id is None:
                continue

            try:
                await self._bot.send_message(
                    chat_id=client.telegram_id,
                    text=f"🛒 Новый заказ №{order_id}",
                )
            except (TelegramAPIError, OSError) as exc:
                logger.warning(
                    "Failed to send Telegram notification",
                    client_id=str(client.id),
                    telegram_id=client.telegram_id,
                    error=str(exc),
                )

    async def order_assembly_started(
        self,
        event: OrderAssemblyStartedEvent | dict,
    ) -> None:
        if isinstance(event, dict):
            order_id = event["order_id"]
            retail_point_id_val = event.get("retail_point_id")
            retail_point_id = (
                UUID(retail_point_id_val)
                if isinstance(retail_point_id_val, str) and retail_point_id_val
                else retail_point_id_val
            )
            created_by_id_val = event.get("created_by_id")
            created_by_id = (
                UUID(created_by_id_val)
                if isinstance(created_by_id_val, str) and created_by_id_val
                else created_by_id_val
            )
        else:
            order_id = event.order_id
            retail_point_id = event.retail_point_id
            created_by_id = event.created_by_id

        recipients = []

        if created_by_id:
            creator_client = await self._clients.get(created_by_id)
            if creator_client and creator_client.telegram_id:
                recipients.append(creator_client)

        if retail_point_id:
            members = await self._retail_point_members.list_members(retail_point_id)
            for member in members:
                client = await self._clients.get(member.client_id)
                if (
                    client
                    and client.telegram_id
                    and client.id not in {r.id for r in recipients}
                ):
                    recipients.append(client)

        for client in recipients:
            try:
                await self._bot.send_message(
                    chat_id=client.telegram_id,
                    text=f"📦 Ваш заказ №{order_id} начал собираться!",
                )
            except (TelegramAPIError, OSError) as exc:
                logger.warning(
                    "Failed to send Telegram notification",
                    client_id=str(client.id),
                    telegram_id=client.telegram_id,
                    error=str(exc),
                )
