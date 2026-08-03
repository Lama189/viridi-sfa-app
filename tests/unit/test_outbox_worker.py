import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.domain.entities.outbox_messages import OutboxMessage
from app.domain.enums import AggregateType, OrderEventType
from app.workers.outbox.worker import OutboxWorker


@pytest.mark.asyncio
async def test_outbox_worker_process_success():
    mock_uow = AsyncMock()
    mock_outbox = AsyncMock()
    mock_uow.outbox = mock_outbox

    mock_publisher = AsyncMock()

    worker = OutboxWorker(uow=mock_uow, publisher=mock_publisher)

    msg = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"order_id": "test_123"},
    )

    await worker._process(msg, mock_uow)

    mock_publisher.publish.assert_called_once_with(msg)
    assert msg.is_processed is True
    mock_outbox.mark_processed.assert_called_once_with(msg.id)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_outbox_worker_run_processes_messages():
    mock_uow = AsyncMock()
    mock_uow.__aenter__.return_value = mock_uow
    mock_outbox = AsyncMock()
    mock_uow.outbox = mock_outbox

    msg = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"order_id": "batch_1"},
    )
    mock_outbox.list_unprocessed.side_effect = [[msg], []]

    mock_publisher = AsyncMock()

    worker = OutboxWorker(uow=mock_uow, publisher=mock_publisher)

    async def stop_worker_after_sleep(duration):
        worker._running = False

    with patch("asyncio.sleep", side_effect=stop_worker_after_sleep):
        await worker.run()

    mock_publisher.publish.assert_called_once_with(msg)
    mock_outbox.mark_processed.assert_called_once_with(msg.id)
    mock_uow.commit.assert_called_once()


@pytest.mark.asyncio
async def test_outbox_worker_run_handles_publisher_error():
    mock_uow = AsyncMock()
    mock_uow.__aenter__.return_value = mock_uow
    mock_outbox = AsyncMock()
    mock_uow.outbox = mock_outbox

    msg = OutboxMessage.create(
        event_type=OrderEventType.CREATED,
        aggregate_type=AggregateType.ORDER,
        aggregate_id=uuid4(),
        payload={"order_id": "err_1"},
    )
    mock_outbox.list_unprocessed.return_value = [msg]

    mock_publisher = AsyncMock()
    mock_publisher.publish.side_effect = Exception("RabbitMQ Connection Failed")

    worker = OutboxWorker(uow=mock_uow, publisher=mock_publisher)

    async def stop_worker_after_sleep(duration):
        worker._running = False

    with patch("asyncio.sleep", side_effect=stop_worker_after_sleep):
        await worker.run()

    mock_publisher.publish.assert_called_once_with(msg)
    mock_outbox.mark_processed.assert_not_called()
    mock_uow.commit.assert_not_called()
