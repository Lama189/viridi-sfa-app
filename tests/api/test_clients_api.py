from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.domain.entities.clients import Client
from app.domain.entities.employees import Employee
from app.infrastructure.postgres.models.enums import EmployeeRole
from app.api.dependencies import get_clients_service, get_clients_auth_service, get_current_user


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def mock_auth_service():
    return AsyncMock()


@pytest.fixture
def mock_admin_employee():
    return Employee(
        id=uuid4(),
        phone="+998900000000",
        password_hash="h",
        role=EmployeeRole.ADMIN,
        full_name="Mock Admin",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_service, mock_auth_service, mock_admin_employee):
    app.dependency_overrides[get_clients_service] = lambda: mock_service
    app.dependency_overrides[get_clients_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_register_success(client, mock_service):
    uid = uuid4()
    mock_service.create_client.return_value = Client(
        phone="+998901234567", full_name="Test", id=uid, is_active=True,
    )

    resp = await client.post("/api/v1/clients/register", json={
        "phone": "+998901234567",
        "full_name": "Test",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["phone"] == "+998901234567"
    assert data["full_name"] == "Test"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client, mock_service):
    mock_service.create_client.side_effect = ValueError("already exists")

    resp = await client.post("/api/v1/clients/register", json={
        "phone": "+998901234567",
        "full_name": "Dup",
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_confirm_success(client, mock_auth_service):
    uid = uuid4()
    from app.api.v1.schemas.clients import ClientWithTokensResponse, ClientResponse
    mock_auth_service.confirm.return_value = ClientWithTokensResponse(
        access_token="acc",
        refresh_token="ref",
        client=ClientResponse(
            id=uid, phone="+998901234567", full_name="Test", telegram_chat_id=123, is_active=True,
        ),
    )

    resp = await client.post("/api/v1/clients/confirm", json={
        "phone": "+998901234567",
        "telegram_chat_id": 123,
        "full_name": "Test",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "acc"
    assert data["refresh_token"] == "ref"


@pytest.mark.asyncio
async def test_confirm_not_found(client, mock_auth_service):
    from app.core.extensions import UserNotFoundError
    mock_auth_service.confirm.side_effect = UserNotFoundError()

    resp = await client.post("/api/v1/clients/confirm", json={
        "phone": "+998900000000",
        "telegram_chat_id": 999,
        "full_name": None,
    })
    assert resp.status_code == 404