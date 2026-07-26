from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.domain.entities.inventory import Product
from app.domain.entities.auth import AuthenticatedEmployee
from app.infrastructure.postgres.models.enums import EmployeeRole
from app.api.dependencies import get_products_service, get_current_user


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
    app.dependency_overrides[get_products_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- POST /api/v1/products ---

@pytest.mark.asyncio
async def test_create_product_success(client, mock_service):
    cat_id = uuid4()
    prod_id = uuid4()
    mock_service.create_product.return_value = Product(
        category_id=cat_id, name="NPK-10", price=Decimal("150.00"), id=prod_id,
    )

    resp = await client.post("/api/v1/products", json={
        "name": "NPK-10",
        "price": 150.00,
        "category_id": str(cat_id),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "NPK-10"
    assert data["price"] == "150.00"


@pytest.mark.asyncio
async def test_create_product_conflict(client, mock_service):
    mock_service.create_product.side_effect = ValueError("already exists")

    resp = await client.post("/api/v1/products", json={
        "name": "Dup",
        "price": 10.00,
        "category_id": str(uuid4()),
    })
    assert resp.status_code == 409


# --- GET /api/v1/products ---

@pytest.mark.asyncio
async def test_get_products(client, mock_service):
    cat_id = uuid4()
    mock_service.get_all_products.return_value = [
        Product(category_id=cat_id, name="A", price=Decimal("1.00")),
        Product(category_id=cat_id, name="B", price=Decimal("2.00")),
    ]

    resp = await client.get("/api/v1/products")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# --- GET /api/v1/products/{id} ---

@pytest.mark.asyncio
async def test_get_product_found(client, mock_service):
    uid = uuid4()
    mock_service.get_by_id.return_value = Product(
        category_id=uuid4(), name="X", price=Decimal("10.00"), id=uid,
    )

    resp = await client.get(f"/api/v1/products/{uid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "X"


@pytest.mark.asyncio
async def test_get_product_not_found(client, mock_service):
    mock_service.get_by_id.return_value = None

    resp = await client.get(f"/api/v1/products/{uuid4()}")
    assert resp.status_code == 404


# --- PATCH /api/v1/products/{id} ---

@pytest.mark.asyncio
async def test_update_product_success(client, mock_service):
    uid = uuid4()
    mock_service.update_product.return_value = Product(
        category_id=uuid4(), name="New", price=Decimal("99.99"), id=uid,
    )

    resp = await client.patch(f"/api/v1/products/{uid}", json={"name": "New", "price": 99.99})
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


@pytest.mark.asyncio
async def test_update_product_not_found(client, mock_service):
    mock_service.update_product.side_effect = ValueError("not found")

    resp = await client.patch(f"/api/v1/products/{uuid4()}", json={"name": "X"})
    assert resp.status_code == 404


# --- DELETE /api/v1/products/{id} ---

@pytest.mark.asyncio
async def test_delete_product_success(client, mock_service):
    resp = await client.delete(f"/api/v1/products/{uuid4()}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_product_not_found(client, mock_service):
    mock_service.delete_product.side_effect = ValueError("not found")

    resp = await client.delete(f"/api/v1/products/{uuid4()}")
    assert resp.status_code == 404
