from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import ClientType
from app.infrastructure.postgres.models.enums import EmployeeRole
from app.api.dependencies import get_retail_points_service, get_current_user


@pytest.fixture
def mock_service():
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
def override_deps(mock_service, mock_admin_employee):
    app.dependency_overrides[get_retail_points_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _retail_point_response(name="Test Point", address="123 Main St"):
    return RetailPoint(
        id=uuid4(),
        name=name,
        address=address,
        client_type=ClientType.C,
        is_active=True,
    )


# --- POST /api/v1/retail_points ---

@pytest.mark.asyncio
async def test_create_retail_point_success(client, mock_service):
    point = _retail_point_response()
    mock_service.create_retail_point.return_value = (point, "INVITE123")

    resp = await client.post("/api/v1/retail_points", json={
        "name": "Test Point",
        "address": "123 Main St",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["retail_point"]["name"] == "Test Point"
    assert data["invite_code"] == "INVITE123"


@pytest.mark.asyncio
async def test_create_retail_point_duplicate(client, mock_service):
    mock_service.create_retail_point.side_effect = ValueError("already exists")

    resp = await client.post("/api/v1/retail_points", json={
        "name": "Duplicate Point",
        "address": "456 Second St",
    })
    assert resp.status_code == 409


# --- GET /api/v1/retail_points/{id} ---

@pytest.mark.asyncio
async def test_get_retail_point_found(client, mock_service):
    point = _retail_point_response()
    mock_service.get_by_id.return_value = point

    resp = await client.get(f"/api/v1/retail_points/{point.id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Point"


@pytest.mark.asyncio
async def test_get_retail_point_not_found(client, mock_service):
    from app.core.extensions import RetailPointNotFoundError
    mock_service.get_by_id.side_effect = RetailPointNotFoundError()

    resp = await client.get(f"/api/v1/retail_points/{uuid4()}")
    assert resp.status_code == 404


# --- GET /api/v1/retail_points/{id}/code ---

@pytest.mark.asyncio
async def test_get_retail_point_invite_code(client, mock_service):
    mock_service.get_retail_point_invite_code.return_value = "INVITE456"

    resp = await client.get(f"/api/v1/retail_points/{uuid4()}/code")
    assert resp.status_code == 200
    assert resp.json()["invite_code"] == "INVITE456"


# --- PATCH /api/v1/retail_points/{id} ---

@pytest.mark.asyncio
async def test_update_retail_point_success(client, mock_service):
    point = _retail_point_response(name="Updated Point")
    mock_service.update_retail_point.return_value = point

    resp = await client.patch(f"/api/v1/retail_points/{point.id}", json={
        "name": "Updated Point",
    })
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Point"


@pytest.mark.asyncio
async def test_update_retail_point_not_found(client, mock_service):
    mock_service.update_retail_point.side_effect = ValueError("not found")

    resp = await client.patch(f"/api/v1/retail_points/{uuid4()}", json={
        "name": "X",
    })
    assert resp.status_code == 404


# --- DELETE /api/v1/retail_points/{id} ---

@pytest.mark.asyncio
async def test_delete_retail_point_success(client, mock_service):
    resp = await client.delete(f"/api/v1/retail_points/{uuid4()}")
    assert resp.status_code == 204
    mock_service.delete_retail_point.assert_called_once()
