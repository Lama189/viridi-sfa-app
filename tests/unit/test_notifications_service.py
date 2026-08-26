from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.dto.notifications import NotificationCreateDTO
from app.application.services.notifications import NotificationsService
from app.core.exceptions import NotificationNotFoundError
from app.domain.entities.notifications import Notification


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.notifications = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return NotificationsService(mock_uow)


@pytest.mark.asyncio
async def test_create_notification(service, mock_uow):
    emp_id = uuid4()
    dto = NotificationCreateDTO(
        employee_id=emp_id,
        title="Новый заказ",
        body="Заказ собран",
        notification_type="order_assigned_to_visit",
        payload={"order_id": "123"},
    )
    result = await service.create(dto)

    assert result.employee_id == emp_id
    assert result.title == "Новый заказ"
    assert result.body == "Заказ собран"
    assert result.notification_type == "order_assigned_to_visit"
    assert result.payload == {"order_id": "123"}
    assert result.is_read is False
    mock_uow.notifications.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_id_success(service, mock_uow):
    notif_id = uuid4()
    notification = Notification(
        id=notif_id,
        employee_id=uuid4(),
        title="Тест",
        body="Тело",
    )
    mock_uow.notifications.get_by_id.return_value = notification

    result = await service.get_by_id(notif_id)
    assert result.id == notif_id
    mock_uow.notifications.get_by_id.assert_awaited_once_with(notif_id)


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    notif_id = uuid4()
    mock_uow.notifications.get_by_id.return_value = None

    with pytest.raises(NotificationNotFoundError):
        await service.get_by_id(notif_id)


@pytest.mark.asyncio
async def test_list_by_employee(service, mock_uow):
    emp_id = uuid4()
    mock_uow.notifications.list_by_employee.return_value = []

    result = await service.list_by_employee(
        emp_id, only_unread=True, limit=10, offset=0
    )
    assert result == []
    mock_uow.notifications.list_by_employee.assert_awaited_once_with(
        employee_id=emp_id,
        only_unread=True,
        limit=10,
        offset=0,
    )


@pytest.mark.asyncio
async def test_count_unread_by_employee(service, mock_uow):
    emp_id = uuid4()
    mock_uow.notifications.count_unread_by_employee.return_value = 5

    count = await service.count_unread_by_employee(emp_id)
    assert count == 5
    mock_uow.notifications.count_unread_by_employee.assert_awaited_once_with(emp_id)


@pytest.mark.asyncio
async def test_mark_as_read(service, mock_uow):
    notif_id = uuid4()
    emp_id = uuid4()
    notification = Notification(
        id=notif_id,
        employee_id=emp_id,
        title="Тест",
        body="Тело",
        is_read=False,
    )
    mock_uow.notifications.get_by_id.return_value = notification

    result = await service.mark_as_read(notif_id, employee_id=emp_id)
    assert result.is_read is True
    assert result.read_at is not None
    mock_uow.notifications.update.assert_awaited_once_with(notification)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_mark_as_read_forbidden_for_other_employee(service, mock_uow):
    notif_id = uuid4()
    notification = Notification(
        id=notif_id,
        employee_id=uuid4(),
        title="Тест",
        body="Тело",
    )
    mock_uow.notifications.get_by_id.return_value = notification

    with pytest.raises(PermissionError, match="Not authorized"):
        await service.mark_as_read(notif_id, employee_id=uuid4())


@pytest.mark.asyncio
async def test_mark_all_as_read(service, mock_uow):
    emp_id = uuid4()
    await service.mark_all_as_read(emp_id)
    mock_uow.notifications.mark_all_as_read.assert_awaited_once_with(emp_id)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete(service, mock_uow):
    notif_id = uuid4()
    emp_id = uuid4()
    notification = Notification(
        id=notif_id,
        employee_id=emp_id,
        title="Тест",
        body="Тело",
    )
    mock_uow.notifications.get_by_id.return_value = notification

    await service.delete(notif_id, employee_id=emp_id)
    mock_uow.notifications.delete.assert_awaited_once_with(notif_id)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_forbidden_for_other_employee(service, mock_uow):
    notif_id = uuid4()
    notification = Notification(
        id=notif_id,
        employee_id=uuid4(),
        title="Тест",
        body="Тело",
    )
    mock_uow.notifications.get_by_id.return_value = notification

    with pytest.raises(PermissionError, match="Not authorized"):
        await service.delete(notif_id, employee_id=uuid4())
