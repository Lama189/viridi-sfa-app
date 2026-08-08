from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_categories_service, get_current_user
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.inventory import Category
from app.domain.enums import EmployeeRole
from app.main import app


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
    app.dependency_overrides[get_categories_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- POST /api/v1/categories ---


@pytest.mark.asyncio
async def test_create_category_success(client, mock_service):
    uid = uuid4()
    mock_service.create_category.return_value = Category(
        name="Fertilizers", id=uid, is_active=True
    )

    resp = await client.post("/api/v1/categories", json={"name": "Fertilizers"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Fertilizers"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_category_duplicate(client, mock_service):
    mock_service.create_category.side_effect = ValueError("already exists")

    resp = await client.post("/api/v1/categories", json={"name": "Seeds"})
    assert resp.status_code == 409


# --- GET /api/v1/categories ---


@pytest.mark.asyncio
async def test_get_categories(client, mock_service):
    mock_service.get_all_categories.return_value = [
        Category(name="A", is_active=True),
        Category(name="B", is_active=True),
    ]

    resp = await client.get("/api/v1/categories")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- GET /api/v1/categories/{id} ---


@pytest.mark.asyncio
async def test_get_category_found(client, mock_service):
    uid = uuid4()
    mock_service.get_by_id.return_value = Category(name="X", id=uid, is_active=True)

    resp = await client.get(f"/api/v1/categories/{uid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "X"


@pytest.mark.asyncio
async def test_get_category_not_found(client, mock_service):
    mock_service.get_by_id.return_value = None

    resp = await client.get(f"/api/v1/categories/{uuid4()}")
    assert resp.status_code == 404


# --- PATCH /api/v1/categories/{id} ---


@pytest.mark.asyncio
async def test_update_category_success(client, mock_service):
    uid = uuid4()
    mock_service.update_category.return_value = Category(
        name="New", id=uid, is_active=True
    )

    resp = await client.patch(f"/api/v1/categories/{uid}", json={"name": "New"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


@pytest.mark.asyncio
async def test_update_category_not_found(client, mock_service):
    mock_service.update_category.side_effect = ValueError("not found")

    resp = await client.patch(f"/api/v1/categories/{uuid4()}", json={"name": "X"})
    assert resp.status_code == 404


# --- DELETE /api/v1/categories/{id} ---


@pytest.mark.asyncio
async def test_delete_category_success(client, mock_service):
    resp = await client.delete(f"/api/v1/categories/{uuid4()}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_category_not_found(client, mock_service):
    mock_service.delete_category.side_effect = ValueError("not found")

    resp = await client.delete(f"/api/v1/categories/{uuid4()}")
    assert resp.status_code == 404
