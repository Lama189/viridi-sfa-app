from aio_pika.abc import AbstractIncomingMessage

from telegram_bot.events.order_events import OrderCreatedEvent, deserialize_event
from telegram_bot.services.notifications import NotificationService


class OrderEventsConsumer:

    def __init__(
        self,
        notification_service: NotificationService,
    ) -> None:
        self._notifications = notification_service

    async def handle(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            event = deserialize_event(message.body, OrderCreatedEvent)

            event_type = getattr(event, "event_type", None)
            if not event_type and isinstance(event, dict):
                event_type = event.get("event_type")

            if not event_type and message.headers:
                event_type = message.headers.get("event_type")

            if not event_type and message.routing_key:
                event_type = message.routing_key

            if event_type == "order.created" or isinstance(event, OrderCreatedEvent):
                await self._notifications.order_created(event)
