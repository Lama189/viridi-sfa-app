from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from aio_pika import ExchangeType

from app.domain.entities.outbox_messages import OutboxMessage
from app.domain.enums import AggregateType, OrderEventType
from app.infrastructure.rabbitmq.publisher import RabbitMQPublisher


@pytest.mark.asyncio
async def test_rabbitmq_publisher_publish_success():
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    mock_channel.declare_exchange.return_value = mock_exchange

    publisher = RabbitMQPublisher(mock_channel)

    message = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"order_id": "123", "amount": 100},
    )

    await publisher.publish(message)

    mock_channel.declare_exchange.assert_called_once_with(
        name="orders",
        type=ExchangeType.TOPIC,
        durable=True,
    )

    mock_exchange.publish.assert_called_once()
    published_msg, routing_key = (
        mock_exchange.publish.call_args[0],
        mock_exchange.publish.call_args[1]["routing_key"],
    )

    assert routing_key == OrderEventType.CREATED
    sent_rabbit_msg = published_msg[0]
    assert sent_rabbit_msg.content_type == "application/json"
    assert sent_rabbit_msg.delivery_mode == 2
    assert sent_rabbit_msg.headers["event_type"] == OrderEventType.CREATED
    assert sent_rabbit_msg.headers["aggregate_type"] == AggregateType.ORDER
    assert sent_rabbit_msg.headers["aggregate_id"] == str(message.aggregate_id)
