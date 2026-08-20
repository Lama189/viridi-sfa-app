import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.workers.order_events.worker import OrderEventsWorker


@pytest.mark.asyncio
async def test_order_events_worker_start_and_stop():
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()
    mock_queue = AsyncMock()
    mock_channel.declare_exchange.return_value = mock_exchange
    mock_channel.declare_queue.return_value = mock_queue
    mock_queue.consume.return_value = "consumer_tag_123"

    mock_assignment_service = AsyncMock()

    worker = OrderEventsWorker(
        channel=mock_channel,
        delivery_assignment_service=mock_assignment_service,
    )

    await worker.start()
    mock_channel.declare_exchange.assert_awaited_once()
    mock_channel.declare_queue.assert_awaited_once()
    mock_queue.bind.assert_awaited_once_with(
        exchange=mock_exchange, routing_key="order.planned"
    )
    mock_queue.consume.assert_awaited_once_with(worker._handle_message)

    await worker.stop()
    mock_queue.cancel.assert_awaited_once_with("consumer_tag_123")


@pytest.mark.asyncio
async def test_order_events_worker_handle_message_success():
    mock_channel = AsyncMock()
    mock_assignment_service = AsyncMock()

    worker = OrderEventsWorker(
        channel=mock_channel,
        delivery_assignment_service=mock_assignment_service,
    )

    order_id = uuid4()
    mock_message = AsyncMock()
    mock_message.body = json.dumps({"order_id": str(order_id)}).encode()
    mock_message.headers = {}
    mock_message.process = MagicMock()
    mock_message.process.return_value.__aenter__ = AsyncMock()
    mock_message.process.return_value.__aexit__ = AsyncMock()

    await worker._handle_message(mock_message)

    mock_assignment_service.assign_order_by_id.assert_awaited_once_with(order_id)


@pytest.mark.asyncio
async def test_order_events_worker_handle_message_from_headers():
    mock_channel = AsyncMock()
    mock_assignment_service = AsyncMock()

    worker = OrderEventsWorker(
        channel=mock_channel,
        delivery_assignment_service=mock_assignment_service,
    )

    order_id = uuid4()
    mock_message = AsyncMock()
    mock_message.body = json.dumps({}).encode()
    mock_message.headers = {"aggregate_id": str(order_id)}
    mock_message.process = MagicMock()
    mock_message.process.return_value.__aenter__ = AsyncMock()
    mock_message.process.return_value.__aexit__ = AsyncMock()

    await worker._handle_message(mock_message)

    mock_assignment_service.assign_order_by_id.assert_awaited_once_with(order_id)


@pytest.mark.asyncio
async def test_order_events_worker_handle_message_no_order_id():
    mock_channel = AsyncMock()
    mock_assignment_service = AsyncMock()

    worker = OrderEventsWorker(
        channel=mock_channel,
        delivery_assignment_service=mock_assignment_service,
    )

    mock_message = AsyncMock()
    mock_message.body = json.dumps({}).encode()
    mock_message.headers = {}
    mock_message.process = MagicMock()
    mock_message.process.return_value.__aenter__ = AsyncMock()
    mock_message.process.return_value.__aexit__ = AsyncMock()

    await worker._handle_message(mock_message)

    mock_assignment_service.assign_order_by_id.assert_not_awaited()
