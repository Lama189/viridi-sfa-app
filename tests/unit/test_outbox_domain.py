from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.domain.entities.outbox_messages import OutboxMessage
from app.domain.enums import AggregateType, OrderEventType


def test_outbox_message_creation():
    agg_id = uuid4()
    msg = OutboxMessage(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=agg_id,
        payload={"order_id": str(agg_id)},
    )

    assert msg.id is not None
    assert msg.event_type == OrderEventType.CREATED
    assert msg.aggregate_type == AggregateType.ORDER
    assert msg.aggregate_id == agg_id
    assert msg.payload == {"order_id": str(agg_id)}
    assert msg.created_at is not None
    assert msg.processed_at is None
    assert msg.is_processed is False


def test_outbox_message_create_classmethod():
    agg_id = uuid4()
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    msg = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=agg_id,
        payload={"test": "data"},
        now=now,
    )

    assert msg.event_type == OrderEventType.CREATED
    assert msg.aggregate_type == AggregateType.ORDER
    assert msg.aggregate_id == agg_id
    assert msg.payload == {"test": "data"}
    assert msg.created_at == now
    assert msg.processed_at is None


def test_outbox_message_mark_processed():
    now = datetime(2026, 1, 1, 12, 5, 0, tzinfo=timezone.utc)
    msg = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={},
    )

    msg.mark_processed(now=now)

    assert msg.processed_at == now
    assert msg.is_processed is True


def test_outbox_message_mark_processed_already_processed_raises():
    msg = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={},
    )
    msg.mark_processed()

    with pytest.raises(ValueError, match="already processed"):
        msg.mark_processed()
