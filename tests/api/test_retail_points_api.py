from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_retail_points_service
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.retail_points import RetailPoint
from app.domain.enums import ClientType, EmployeeRole
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

    resp = await client.post(
        "/api/v1/retail_points",
        json={
            "name": "Test Point",
            "address": "123 Main St",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["retail_point"]["name"] == "Test Point"
    assert data["invite_code"] == "INVITE123"


@pytest.mark.asyncio
async def test_create_retail_point_duplicate(client, mock_service):
    mock_service.create_retail_point.side_effect = ValueError("already exists")

    resp = await client.post(
        "/api/v1/retail_points",
        json={
            "name": "Duplicate Point",
            "address": "456 Second St",
        },
    )
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
    from app.core.exceptions import RetailPointNotFoundError

    mock_service.get_by_id.side_effect = RetailPointNotFoundError()

    resp = await client.get(f"/api/v1/retail_points/{uuid4()}")
    assert resp.status_code == 404


# --- GET /api/v1/retail_points/{id}/details ---


@pytest.mark.asyncio
async def test_get_retail_point_details(client, mock_service):
    from datetime import UTC, datetime
    from decimal import Decimal

    from app.domain.entities.orders import Order
    from app.domain.entities.retail_points import RetailPointDetails
    from app.domain.entities.visit_debts import VisitDebt

    point = _retail_point_response()
    order = Order(
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=point.id,
        total_amount=Decimal("250000.00"),
        total_volume=Decimal("2.500"),
        created_at=datetime.now(UTC),
    )
    debt = VisitDebt(
        visit_id=uuid4(),
        amount=Decimal("50000.00"),
        comment="Unpaid",
    )
    mock_service.get_details.return_value = RetailPointDetails(
        retail_point=point,
        orders=[order],
        debts=[debt],
    )

    resp = await client.get(f"/api/v1/retail_points/{point.id}/details")

    assert resp.status_code == 200
    data = resp.json()
    assert data["retail_point"]["id"] == str(point.id)
    assert data["orders"][0]["id"] == str(order.id)
    assert data["orders"][0]["total_amount"] == "250000.00"
    assert data["debts"][0]["id"] == str(debt.id)
    assert data["debts"][0]["amount"] == "50000.00"
    mock_service.get_details.assert_awaited_once_with(point.id)


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

    resp = await client.patch(
        f"/api/v1/retail_points/{point.id}",
        json={
            "name": "Updated Point",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Point"


@pytest.mark.asyncio
async def test_update_retail_point_not_found(client, mock_service):
    mock_service.update_retail_point.side_effect = ValueError("not found")

    resp = await client.patch(
        f"/api/v1/retail_points/{uuid4()}",
        json={
            "name": "X",
        },
    )
    assert resp.status_code == 404


# --- DELETE /api/v1/retail_points/{id} ---


@pytest.mark.asyncio
async def test_delete_retail_point_success(client, mock_service):
    resp = await client.delete(f"/api/v1/retail_points/{uuid4()}")
    assert resp.status_code == 204
    mock_service.delete_retail_point.assert_called_once()


# --- GET /api/v1/retail_points/by-weekday/{weekday} ---


@pytest.mark.asyncio
async def test_list_retail_points_by_weekday(client, mock_service, mock_admin_employee):
    from app.domain.enums import Weekday

    point = _retail_point_response(name="Monday Store")
    mock_service.list_by_employee_and_weekday.return_value = [point]

    resp = await client.get("/api/v1/retail_points/by-weekday/0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Monday Store"
    mock_service.list_by_employee_and_weekday.assert_called_once_with(
        employee_id=mock_admin_employee.id,
        weekday=Weekday.MONDAY,
    )


@pytest.mark.asyncio
async def test_list_retail_points_returns_total_debt(
    client, mock_service, mock_admin_employee
):
    point = _retail_point_response(name="Store with Debt")
    point.total_debt = Decimal("250000.00")
    mock_service.list_retail_points.return_value = [point]

    resp = await client.get("/api/v1/retail_points")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Store with Debt"
    assert data[0]["total_debt"] == "250000.00"


@pytest.mark.asyncio
async def test_list_debtors_api(client, mock_service, mock_admin_employee):
    from app.application.dto.retail_points import (
        RetailPointDebtorDTO,
        RetailPointShortDTO,
    )
    from app.domain.entities.visit_debts import VisitDebt

    point_id = uuid4()
    debt = VisitDebt(
        visit_id=uuid4(), amount=Decimal("150000.00"), comment="Invoice #1"
    )
    debtor = RetailPointDebtorDTO(
        retail_point=RetailPointShortDTO(
            id=point_id,
            name="Store Debtor",
            address="Addr 123",
            contact_person="John",
            phone_number="+998901234567",
        ),
        total_debt=Decimal("150000.00"),
        debts_count=1,
        debts=[debt],
    )
    mock_service.list_debtors.return_value = [debtor]

    resp = await client.get("/api/v1/retail_points/debtors")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["retail_point"]["name"] == "Store Debtor"
    assert data[0]["retail_point"]["contact_person"] == "John"
    assert data[0]["total_debt"] == "150000.00"
    assert data[0]["debts_count"] == 1
    assert len(data[0]["debts"]) == 1
    assert data[0]["debts"][0]["amount"] == "150000.00"
    assert data[0]["debts"][0]["comment"] == "Invoice #1"
    mock_service.list_debtors.assert_called_once_with(
        employee_id=mock_admin_employee.id,
        role=mock_admin_employee.role,
        filter_employee_id=None,
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_retail_point_debts(client):
    from decimal import Decimal

    from app.api.dependencies import get_visit_debts_service
    from app.domain.entities.visit_debts import VisitDebt

    mock_debt_service = AsyncMock()
    point_id = uuid4()
    debt = VisitDebt(
        visit_id=uuid4(), amount=Decimal("150000.00"), comment="Unpaid invoice"
    )
    mock_debt_service.list_by_retail_point.return_value = [debt]

    app.dependency_overrides[get_visit_debts_service] = lambda: mock_debt_service

    resp = await client.get(f"/api/v1/retail_points/{point_id}/debts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["amount"] == "150000.00"
    mock_debt_service.list_by_retail_point.assert_called_once_with(point_id)


@pytest.mark.asyncio
async def test_assign_agent_to_retail_point(client):
    from app.api.dependencies import get_retail_point_assignment_service
    from app.domain.entities.retail_point_assignments import RetailPointAssignment

    mock_assign_service = AsyncMock()
    point_id = uuid4()
    agent_id = uuid4()
    assignment = RetailPointAssignment(
        id=uuid4(), retail_point_id=point_id, employee_id=agent_id
    )
    mock_assign_service.assign_employee.return_value = assignment

    app.dependency_overrides[get_retail_point_assignment_service] = lambda: (
        mock_assign_service
    )

    resp = await client.post(
        f"/api/v1/retail_points/{point_id}/assign-agent",
        json={"employee_id": str(agent_id)},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["retail_point_id"] == str(point_id)
    assert data["employee_id"] == str(agent_id)
    mock_assign_service.assign_employee.assert_called_once_with(point_id, agent_id)


@pytest.mark.asyncio
async def test_list_retail_point_orders(client):
    from app.api.dependencies import get_orders_service

    mock_orders_service = AsyncMock()
    point_id = uuid4()
    mock_orders_service.list_by_retail_point.return_value = []

    app.dependency_overrides[get_orders_service] = lambda: mock_orders_service

    resp = await client.get(f"/api/v1/retail_points/{point_id}/orders")
    assert resp.status_code == 200
    assert resp.json() == []
    mock_orders_service.list_by_retail_point.assert_called_once_with(point_id)
