from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.outbox_messages import OutboxMessage
from app.domain.enums import AggregateType, OrderEventType
from app.infrastructure.postgres.repos.outbox import PostgresOutboxRepository


@pytest.mark.asyncio
async def test_add_and_list_unprocessed(
    session: AsyncSession,
    outbox_repo: PostgresOutboxRepository,
):
    msg1 = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"key": "val1"},
    )
    msg2 = OutboxMessage.create(
        event_type=OrderEventType.DELIVERED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"key": "val2"},
    )

    await outbox_repo.add(msg1)
    await outbox_repo.add(msg2)
    await session.commit()

    unprocessed = await outbox_repo.list_unprocessed(limit=10)
    assert len(unprocessed) == 2
    assert unprocessed[0].id == msg1.id
    assert unprocessed[0].event_type == OrderEventType.CREATED
    assert unprocessed[0].payload == {"key": "val1"}
    assert unprocessed[1].id == msg2.id


@pytest.mark.asyncio
async def test_list_unprocessed_limit(
    session: AsyncSession,
    outbox_repo: PostgresOutboxRepository,
):
    for i in range(5):
        msg = OutboxMessage.create(
            event_type=OrderEventType.CREATED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=uuid4(),
            payload={"idx": i},
        )
        await outbox_repo.add(msg)
    await session.commit()

    unprocessed = await outbox_repo.list_unprocessed(limit=3)
    assert len(unprocessed) == 3


@pytest.mark.asyncio
async def test_mark_processed(
    session: AsyncSession,
    outbox_repo: PostgresOutboxRepository,
):
    msg1 = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"msg": 1},
    )
    msg2 = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"msg": 2},
    )

    await outbox_repo.add(msg1)
    await outbox_repo.add(msg2)
    await session.commit()

    await outbox_repo.mark_processed(msg1.id)
    await session.commit()

    unprocessed = await outbox_repo.list_unprocessed(limit=10)
    assert len(unprocessed) == 1
    assert unprocessed[0].id == msg2.id
