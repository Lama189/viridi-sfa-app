from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import allow_all_staff, get_warehouses_service
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.inventory import Warehouse
from app.domain.enums import EmployeeRole
from app.main import app


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture(autouse=True)
def override_deps(mock_service):
    app.dependency_overrides[get_warehouses_service] = lambda: mock_service
    app.dependency_overrides[allow_all_staff] = lambda: AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000000",
        role=EmployeeRole.ADMIN,
        full_name="Admin",
        is_active=True,
    )
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- POST /api/v1/warehouses ---


@pytest.mark.asyncio
async def test_create_warehouse_success(client, mock_service):
    uid = uuid4()
    mock_service.create_warehouse.return_value = Warehouse(
        name="WH-1", address="addr", id=uid, is_active=True
    )

    resp = await client.post(
        "/api/v1/warehouses", json={"name": "WH-1", "address": "addr"}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "WH-1"


# --- GET /api/v1/warehouses ---


@pytest.mark.asyncio
async def test_get_warehouses(client, mock_service):
    warehouses = [
        Warehouse(name="A"),
        Warehouse(name="B"),
    ]
    mock_service.list.return_value = warehouses
    mock_service.get_all_warehouses.return_value = warehouses

    resp = await client.get("/api/v1/warehouses")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- GET /api/v1/warehouses/{id} ---


@pytest.mark.asyncio
async def test_get_warehouse_found(client, mock_service):
    uid = uuid4()
    mock_service.get_by_id.return_value = Warehouse(name="X", id=uid, is_active=True)

    resp = await client.get(f"/api/v1/warehouses/{uid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "X"


@pytest.mark.asyncio
async def test_get_warehouse_not_found(client, mock_service):
    mock_service.get_by_id.return_value = None

    resp = await client.get(f"/api/v1/warehouses/{uuid4()}")
    assert resp.status_code == 404


# --- PATCH /api/v1/warehouses/{id} ---


@pytest.mark.asyncio
async def test_update_warehouse_success(client, mock_service):
    uid = uuid4()
    mock_service.update_warehouse.return_value = Warehouse(
        name="New", id=uid, is_active=True
    )

    resp = await client.patch(f"/api/v1/warehouses/{uid}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


@pytest.mark.asyncio
async def test_update_warehouse_not_found(client, mock_service):
    mock_service.update_warehouse.side_effect = ValueError("not found")

    resp = await client.patch(f"/api/v1/warehouses/{uuid4()}", json={"name": "X"})
    assert resp.status_code == 404
