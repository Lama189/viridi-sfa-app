from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_current_employee,
    get_notifications_service,
)
from app.core.exceptions import NotificationNotFoundError
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.notifications import Notification
from app.domain.enums import EmployeeRole
from app.main import app


@pytest.fixture
def mock_notifications_service():
    return AsyncMock()


@pytest.fixture
def mock_agent_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000001",
        role=EmployeeRole.AGENT,
        full_name="Mock Agent",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_notifications_service, mock_agent_employee):
    app.dependency_overrides[get_notifications_service] = lambda: (
        mock_notifications_service
    )
    app.dependency_overrides[get_current_employee] = lambda: mock_agent_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_notifications(
    client, mock_notifications_service, mock_agent_employee
):
    notif = Notification(
        id=uuid4(),
        employee_id=mock_agent_employee.id,
        title="Новый заказ",
        body="Собран заказ",
        notification_type="order_assigned_to_visit",
        payload={"order_id": "123"},
    )
    mock_notifications_service.list_by_employee.return_value = [notif]

    resp = await client.get("/api/v1/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(notif.id)
    assert data[0]["title"] == "Новый заказ"
    assert data[0]["payload"] == {"order_id": "123"}
    mock_notifications_service.list_by_employee.assert_awaited_once_with(
        employee_id=mock_agent_employee.id,
        only_unread=False,
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_get_unread_count(
    client, mock_notifications_service, mock_agent_employee
):
    mock_notifications_service.count_unread_by_employee.return_value = 3

    resp = await client.get("/api/v1/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.json()["unread_count"] == 3
    mock_notifications_service.count_unread_by_employee.assert_awaited_once_with(
        mock_agent_employee.id
    )


@pytest.mark.asyncio
async def test_mark_notification_as_read_success(
    client, mock_notifications_service, mock_agent_employee
):
    notif = Notification(
        id=uuid4(),
        employee_id=mock_agent_employee.id,
        title="Новый заказ",
        body="Собран заказ",
        is_read=True,
    )
    mock_notifications_service.mark_as_read.return_value = notif

    resp = await client.post(f"/api/v1/notifications/{notif.id}/read")
    assert resp.status_code == 200
    assert resp.json()["is_read"] is True
    mock_notifications_service.mark_as_read.assert_awaited_once_with(
        notification_id=notif.id, employee_id=mock_agent_employee.id
    )


@pytest.mark.asyncio
async def test_mark_notification_as_read_forbidden_for_other_employee(
    client, mock_notifications_service
):
    mock_notifications_service.mark_as_read.side_effect = PermissionError(
        "Not authorized to access this notification"
    )

    resp = await client.post(f"/api/v1/notifications/{uuid4()}/read")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_mark_notification_as_read_not_found(client, mock_notifications_service):
    mock_notifications_service.mark_as_read.side_effect = NotificationNotFoundError()

    resp = await client.post(f"/api/v1/notifications/{uuid4()}/read")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_mark_all_as_read(
    client, mock_notifications_service, mock_agent_employee
):
    resp = await client.post("/api/v1/notifications/read-all")
    assert resp.status_code == 204
    mock_notifications_service.mark_all_as_read.assert_awaited_once_with(
        mock_agent_employee.id
    )


@pytest.mark.asyncio
async def test_delete_notification_success(
    client, mock_notifications_service, mock_agent_employee
):
    notif_id = uuid4()
    resp = await client.delete(f"/api/v1/notifications/{notif_id}")
    assert resp.status_code == 204
    mock_notifications_service.delete.assert_awaited_once_with(
        notification_id=notif_id, employee_id=mock_agent_employee.id
    )
