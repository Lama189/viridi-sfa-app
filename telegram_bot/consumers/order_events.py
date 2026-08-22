from aio_pika.abc import AbstractIncomingMessage

from telegram_bot.events.order_events import (
    OrderAssembledEvent,
    OrderAssemblyStartedEvent,
    OrderCancelledEvent,
    OrderCreatedEvent,
    OrderDeliveredEvent,
    OrderPlannedEvent,
    OrderTakenByAgentEvent,
    deserialize_event,
)
from telegram_bot.services.notifications import NotificationService


class OrderEventsConsumer:
    def __init__(
        self,
        notification_service: NotificationService,
    ) -> None:
        self._notifications = notification_service

    async def handle(self, message: AbstractIncomingMessage) -> None:
        async with message.process():
            event = deserialize_event(message.body)

            event_type = getattr(event, "event_type", None)
            if not event_type and isinstance(event, dict):
                event_type = event.get("event_type")

            if not event_type and message.headers:
                event_type = message.headers.get("event_type")

            if not event_type and message.routing_key:
                event_type = message.routing_key

            if event_type == "order.assembly_started" or isinstance(
                event, OrderAssemblyStartedEvent
            ):
                await self._notifications.order_assembly_started(event)
            elif event_type == "order.created" or isinstance(event, OrderCreatedEvent):
                await self._notifications.order_created(event)
            elif event_type == "order.planned" or isinstance(event, OrderPlannedEvent):
                await self._notifications.order_planned(event)
            elif event_type == "order.assembled" or isinstance(
                event, OrderAssembledEvent
            ):
                await self._notifications.order_assembled(event)
            elif event_type == "order.taken_by_agent" or isinstance(
                event, OrderTakenByAgentEvent
            ):
                await self._notifications.order_taken_by_agent(event)
            elif event_type == "order.delivered" or isinstance(
                event, OrderDeliveredEvent
            ):
                await self._notifications.order_delivered(event)
            elif event_type == "order.cancelled" or isinstance(
                event, OrderCancelledEvent
            ):
                await self._notifications.order_cancelled(event)
