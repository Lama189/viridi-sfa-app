from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.domain.entities.auth import AuthenticatedEmployee
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
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000000",
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
async def test_register_success(client, mock_auth_service):
    from app.api.v1.schemas.clients import ClientWithTokensResponse, ClientResponse
    uid = uuid4()
    mock_auth_service.register.return_value = ClientWithTokensResponse(
        access_token="acc",
        refresh_token="ref",
        client=ClientResponse(
            id=uid, phone="+998901234567", full_name="Test", telegram_chat_id=None, is_active=True,
        ),
    )

    resp = await client.post("/api/v1/clients/register", json={
        "invite_code": "ABC123",
        "phone": "+998901234567",
        "full_name": "Test",
        "telegram_chat_id": 123,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["access_token"] == "acc"
    assert data["refresh_token"] == "ref"
    assert data["client"]["phone"] == "+998901234567"


@pytest.mark.asyncio
async def test_register_duplicate_phone(client, mock_auth_service):
    from app.core.extensions import UserAlreadyExistsError
    mock_auth_service.register.side_effect = UserAlreadyExistsError()

    resp = await client.post("/api/v1/clients/register", json={
        "invite_code": "ABC123",
        "phone": "+998901234567",
        "full_name": "Dup",
        "telegram_chat_id": 111,
    })
    assert resp.status_code == 409