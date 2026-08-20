from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_stocks_service
from app.application.dto.categories import CategoryDTO
from app.application.dto.stocks import ProductWithStockDTO, StockSummaryDTO
from app.application.dto.warehouses import WarehouseShortDTO
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.stocks import Stock, StockTransaction
from app.domain.enums import (
    EmployeeRole,
    StockReferenceType,
    StockTransactionType,
    TransactionActorType,
)
from app.main import app


@pytest.fixture
def mock_stocks_service():
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
def override_deps(mock_stocks_service, mock_admin_employee):
    app.dependency_overrides[get_stocks_service] = lambda: mock_stocks_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_list_stock_transactions(client, mock_stocks_service):
    tx = StockTransaction(
        warehouse_id=uuid4(),
        product_id=uuid4(),
        quantity_delta=100,
        transaction_type=StockTransactionType.RECEIPT,
        reference_type=StockReferenceType.RECEIPT,
        reference_id=uuid4(),
        actor_type=TransactionActorType.EMPLOYEE,
    )
    mock_stocks_service.list_transactions.return_value = [tx]

    resp = await client.get("/api/v1/stocks/transactions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["quantity_delta"] == 100
    assert data[0]["transaction_type"] == "receipt"


@pytest.mark.asyncio
async def test_adjust_stock(client, mock_stocks_service, mock_admin_employee):
    wh_id = uuid4()
    p_id = uuid4()
    stock = Stock(warehouse_id=wh_id, product_id=p_id, quantity=50, reserved_quantity=0)
    mock_stocks_service.adjust_stock.return_value = stock

    resp = await client.post(
        "/api/v1/stocks/adjust",
        json={
            "warehouse_id": str(wh_id),
            "product_id": str(p_id),
            "new_quantity": 50,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == 50
    mock_stocks_service.adjust_stock.assert_called_once_with(
        warehouse_id=wh_id,
        product_id=p_id,
        new_quantity=50,
        actor_id=mock_admin_employee.id,
        reference_id=None,
    )


@pytest.mark.asyncio
async def test_add_stock(client, mock_stocks_service, mock_admin_employee):
    wh_id = uuid4()
    p_id = uuid4()
    stock = Stock(
        warehouse_id=wh_id, product_id=p_id, quantity=100, reserved_quantity=0
    )
    mock_stocks_service.add_stock.return_value = stock

    resp = await client.post(
        "/api/v1/stocks/replenish",
        json={
            "warehouse_id": str(wh_id),
            "product_id": str(p_id),
            "quantity": 50,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == 100
    mock_stocks_service.add_stock.assert_called_once()
    dto = mock_stocks_service.add_stock.call_args[0][0]
    assert dto.warehouse_id == wh_id
    assert dto.product_id == p_id
    assert dto.quantity == 50
    assert dto.created_by_id == mock_admin_employee.id


@pytest.mark.asyncio
async def test_write_off_stock_admin(client, mock_stocks_service, mock_admin_employee):
    wh_id = uuid4()
    p_id = uuid4()
    stock = Stock(warehouse_id=wh_id, product_id=p_id, quantity=80, reserved_quantity=0)
    mock_stocks_service.write_off.return_value = stock

    resp = await client.post(
        "/api/v1/stocks/write-off",
        json={
            "warehouse_id": str(wh_id),
            "product_id": str(p_id),
            "quantity": 20,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["quantity"] == 80
    mock_stocks_service.write_off.assert_called_once()
    dto = mock_stocks_service.write_off.call_args[0][0]
    assert dto.warehouse_id == wh_id
    assert dto.product_id == p_id
    assert dto.quantity == 20
    assert dto.created_by_id == mock_admin_employee.id


@pytest.mark.asyncio
async def test_write_off_stock_forbidden_for_agent(client, mock_stocks_service):
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedEmployee(
        id=uuid4(),
        phone="+998901234567",
        role=EmployeeRole.AGENT,
        full_name="Agent",
        is_active=True,
    )
    wh_id = uuid4()
    p_id = uuid4()

    resp = await client.post(
        "/api/v1/stocks/write-off",
        json={
            "warehouse_id": str(wh_id),
            "product_id": str(p_id),
            "quantity": 20,
        },
    )
    assert resp.status_code == 403
    mock_stocks_service.write_off.assert_not_called()


@pytest.mark.asyncio
async def test_list_warehouse_stocks(client, mock_stocks_service):
    wh_id = uuid4()
    mock_stocks_service.get_warehouse_inventory.return_value = []

    resp = await client.get(f"/api/v1/stocks?warehouse_id={wh_id}")
    assert resp.status_code == 200
    assert resp.json() == []
    mock_stocks_service.get_warehouse_inventory.assert_called_once_with(
        warehouse_id=wh_id
    )


@pytest.mark.asyncio
async def test_list_warehouse_stocks_with_data(client, mock_stocks_service):
    wh_id = uuid4()
    p_id = uuid4()
    cat_id = uuid4()

    mock_dto = ProductWithStockDTO(
        id=p_id,
        name="Test Product",
        price=Decimal("100.00"),
        volume=Decimal("1.500"),
        weight=Decimal("2.000"),
        items_in_box=10,
        category=CategoryDTO(id=cat_id, name="Test Cat", is_active=True),
        photo_url=None,
        stock=StockSummaryDTO(
            warehouse=WarehouseShortDTO(id=wh_id, name="Central WH"),
            quantity=1000,
            reserved_quantity=100,
            available_quantity=900,
            updated_at=None,
        ),
    )
    mock_stocks_service.get_warehouse_inventory.return_value = [mock_dto]

    resp = await client.get(f"/api/v1/stocks?warehouse_id={wh_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == str(p_id)
    assert data[0]["name"] == "Test Product"
    assert data[0]["stock"]["warehouse"]["id"] == str(wh_id)
    assert data[0]["stock"]["warehouse"]["name"] == "Central WH"
    assert data[0]["stock"]["quantity"] == 1000
    assert data[0]["stock"]["reserved_quantity"] == 100
    assert data[0]["stock"]["available_quantity"] == 900
