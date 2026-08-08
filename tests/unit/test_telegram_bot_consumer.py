from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from telegram_bot.consumers.order_events import OrderEventsConsumer
from telegram_bot.events.order_events import (
    OrderAssemblyStartedEvent,
    OrderCreatedEvent,
    deserialize_event,
)
from telegram_bot.services.clients import ClientDTO
from telegram_bot.services.notifications import NotificationService
from telegram_bot.services.retail_point_members import RetailPointMemberDTO


def test_deserialize_order_created_event():
    order_id = uuid4()
    retail_point_id = uuid4()
    created_by_id = uuid4()
    warehouse_id = uuid4()

    body = (
        f'{{"order_id": "{order_id}", "retail_point_id": "{retail_point_id}", '
        f'"created_by_id": "{created_by_id}", "warehouse_id": "{warehouse_id}"}}'
    ).encode()

    event = deserialize_event(body, OrderCreatedEvent)

    assert isinstance(event, OrderCreatedEvent)
    assert event.order_id == order_id
    assert event.retail_point_id == retail_point_id
    assert event.created_by_id == created_by_id
    assert event.warehouse_id == warehouse_id
    assert event.event_type == "order.created"


@pytest.mark.asyncio
async def test_order_events_consumer_handle_order_created():
    mock_notifications = AsyncMock(spec=NotificationService)
    consumer = OrderEventsConsumer(notification_service=mock_notifications)

    order_id = uuid4()
    retail_point_id = uuid4()
    created_by_id = uuid4()

    body = (
        f'{{"order_id": "{order_id}", "retail_point_id": "{retail_point_id}", '
        f'"created_by_id": "{created_by_id}"}}'
    ).encode()

    mock_message = MagicMock()
    mock_message.body = body
    mock_message.headers = {"event_type": "order.created"}
    mock_message.routing_key = "order.created"

    process_cm = AsyncMock()
    mock_message.process.return_value = process_cm

    await consumer.handle(mock_message)

    mock_notifications.order_created.assert_called_once()
    called_event = mock_notifications.order_created.call_args[0][0]
    assert isinstance(called_event, OrderCreatedEvent)
    assert called_event.order_id == order_id
    assert called_event.retail_point_id == retail_point_id


@pytest.mark.asyncio
async def test_notification_service_order_created():
    mock_bot = AsyncMock()
    mock_retail_point_members = AsyncMock()
    mock_clients = AsyncMock()

    order_id = uuid4()
    retail_point_id = uuid4()
    client_id_1 = uuid4()
    client_id_2 = uuid4()

    # Member 1 with telegram_id
    member_1 = RetailPointMemberDTO(
        id=uuid4(), retail_point_id=retail_point_id, client_id=client_id_1
    )
    client_1 = ClientDTO(
        id=client_id_1,
        phone="+998901111111",
        full_name="Client One",
        telegram_id=12345678,
    )

    # Member 2 without telegram_id
    member_2 = RetailPointMemberDTO(
        id=uuid4(), retail_point_id=retail_point_id, client_id=client_id_2
    )
    client_2 = ClientDTO(
        id=client_id_2, phone="+998902222222", full_name="Client Two", telegram_id=None
    )

    # Setup mocks
    mock_retail_point_members.list_members.return_value = [member_1, member_2]

    async def get_client_by_id(cid):
        if cid == client_id_1:
            return client_1
        if cid == client_id_2:
            return client_2
        return None

    mock_clients.get.side_effect = get_client_by_id

    notification_service = NotificationService(
        bot=mock_bot,
        retail_point_members=mock_retail_point_members,
        clients=mock_clients,
    )
    event = OrderCreatedEvent(
        order_id=order_id,
        retail_point_id=retail_point_id,
        created_by_id=client_id_1,
    )

    await notification_service.order_created(event)

    # Only client_1 has telegram_id (12345678), so send_message should be called once
    mock_bot.send_message.assert_called_once_with(
        chat_id=12345678,
        text=f"🛒 Новый заказ №{order_id}",
    )


def test_deserialize_order_assembly_started_event():
    order_id = uuid4()
    retail_point_id = uuid4()
    created_by_id = uuid4()
    employee_id = uuid4()

    body = (
        f'{{"order_id": "{order_id}", "retail_point_id": "{retail_point_id}", '
        f'"created_by_id": "{created_by_id}", "employee_id": "{employee_id}", '
        f'"event_type": "order.assembly_started"}}'
    ).encode()

    event = deserialize_event(body)

    assert isinstance(event, OrderAssemblyStartedEvent)
    assert event.order_id == order_id
    assert event.retail_point_id == retail_point_id
    assert event.created_by_id == created_by_id
    assert event.employee_id == employee_id
    assert event.event_type == "order.assembly_started"


@pytest.mark.asyncio
async def test_order_events_consumer_handle_order_assembly_started():
    mock_notifications = AsyncMock(spec=NotificationService)
    consumer = OrderEventsConsumer(notification_service=mock_notifications)

    order_id = uuid4()
    body = f'{{"order_id": "{order_id}", "event_type": "order.assembly_started"}}'.encode()

    mock_message = MagicMock()
    mock_message.body = body
    mock_message.headers = {"event_type": "order.assembly_started"}
    mock_message.routing_key = "order.assembly_started"

    process_cm = AsyncMock()
    mock_message.process.return_value = process_cm

    await consumer.handle(mock_message)

    mock_notifications.order_assembly_started.assert_called_once()


@pytest.mark.asyncio
async def test_notification_service_order_assembly_started():
    mock_bot = AsyncMock()
    mock_retail_point_members = AsyncMock()
    mock_clients = AsyncMock()

    order_id = uuid4()
    client_id = uuid4()

    client = ClientDTO(
        id=client_id,
        phone="+998901111111",
        full_name="Client One",
        telegram_id=987654321,
    )
    mock_clients.get.return_value = client
    mock_retail_point_members.list_members.return_value = []

    notification_service = NotificationService(
        bot=mock_bot,
        retail_point_members=mock_retail_point_members,
        clients=mock_clients,
    )
    event = OrderAssemblyStartedEvent(
        order_id=order_id,
        created_by_id=client_id,
    )

    await notification_service.order_assembly_started(event)

    mock_bot.send_message.assert_called_once_with(
        chat_id=987654321,
        text=f"📦 Ваш заказ №{order_id} начал собираться!",
    )
