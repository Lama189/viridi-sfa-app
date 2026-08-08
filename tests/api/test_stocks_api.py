from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_stocks_service
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
