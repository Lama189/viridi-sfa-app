from uuid import UUID

from aiogram import Bot

from telegram_bot.events.order_events import OrderCreatedEvent
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
            except Exception:  # noqa: BLE001, S110
                pass
