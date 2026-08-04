from aio_pika import ExchangeType, Message
from aio_pika.abc import AbstractChannel

from app.application.interfaces.publisher import IPublisher
from app.core.observability.logging import logger
from app.domain.entities.outbox_messages import OutboxMessage
from app.infrastructure.rabbitmq.serializer import serialize_event


class RabbitMQPublisher(IPublisher):
    def __init__(self, channel: AbstractChannel) -> None:
        self._channel = channel

    async def publish(self, message: OutboxMessage) -> None:
        exchange = await self._channel.declare_exchange(
            name="orders", type=ExchangeType.TOPIC, durable=True
        )

        rebbit_message = Message(
            body=serialize_event(message.payload),
            content_type="application/json",
            delivery_mode=2,
            headers={
                "event_type": message.event_type,
                "aggregate_type": message.aggregate_type,
                "aggregate_id": str(message.aggregate_id),
            },
        )

        logger.info(
            "Publishing event",
            event_type=message.event_type,
            aggregate_id=str(message.aggregate_id),
        )

        await exchange.publish(rebbit_message, routing_key=message.event_type)
