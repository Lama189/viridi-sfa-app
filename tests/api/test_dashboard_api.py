from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    allow_all_staff,
    get_current_user,
    get_dashboard_service,
)
from app.api.v1.schemas.dashboard import CategoryReportDTO, DailyReportDTO
from app.application.interfaces.services.dashboard import EmployeeDashboard
from app.core.exceptions import VisitPlanNotFoundError
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import EmployeeRole
from app.main import app


@pytest.fixture
def mock_dashboard_service():
    return AsyncMock()


@pytest.fixture
def mock_agent_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998901234567",
        role=EmployeeRole.AGENT,
        full_name="Agent Tester",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_dashboard_service, mock_agent_employee):
    app.dependency_overrides[get_dashboard_service] = lambda: mock_dashboard_service
    app.dependency_overrides[get_current_user] = lambda: mock_agent_employee
    app.dependency_overrides[allow_all_staff] = lambda: mock_agent_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_dashboard_success(
    client, mock_dashboard_service, mock_agent_employee
):
    mock_dashboard_service.get_employee_dashboard.return_value = EmployeeDashboard(
        total_points=25,
        completed_points=12,
        remaining_points=13,
        completion_percentage=Decimal(48),
        orders_count=8,
        orders_amount=Decimal("1250000.00"),
        debts_count=3,
    )

    response = await client.get("/api/v1/dashboard")

    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 25
    assert data["completed_points"] == 12
    assert data["remaining_points"] == 13
    assert (
        data["completion_percentage"] == "48"
        or data["completion_percentage"] == 48
        or float(data["completion_percentage"]) == 48.0
    )
    assert data["orders_count"] == 8
    assert float(data["orders_amount"]) == 1250000.0
    assert data["debts_count"] == 3

    mock_dashboard_service.get_employee_dashboard.assert_awaited_once_with(
        mock_agent_employee.id
    )


@pytest.mark.asyncio
async def test_get_dashboard_plan_not_found(client, mock_dashboard_service):
    mock_dashboard_service.get_employee_dashboard.side_effect = VisitPlanNotFoundError()

    response = await client.get("/api/v1/dashboard")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Visit plan not found"


@pytest.mark.asyncio
async def test_get_daily_report_success(
    client, mock_dashboard_service, mock_agent_employee
):
    date_from = "2026-07-31T00:00:00Z"
    date_to = "2026-07-31T23:59:59Z"
    cat_id = uuid4()

    mock_dashboard_service.get_agent_daily_report.return_value = DailyReportDTO(
        total_amount=Decimal("300000.00"),
        acb_count=5,
        total_quantity_pcs=100,
        total_volume_boxes=Decimal("10.0"),
        categories=[
            CategoryReportDTO(
                category_id=cat_id,
                category_name="Beverages",
                quantity_pcs=100,
                volume_boxes=Decimal("10.0"),
                total_amount=Decimal("300000.00"),
            )
        ],
    )

    response = await client.get(
        "/api/v1/dashboard/daily-report",
        params={"date_from": date_from, "date_to": date_to},
    )

    assert response.status_code == 200
    data = response.json()
    assert float(data["total_amount"]) == 300000.0
    assert data["acb_count"] == 5
    assert data["total_quantity_pcs"] == 100
    assert float(data["total_volume_boxes"]) == 10.0
    assert len(data["categories"]) == 1
    assert data["categories"][0]["category_name"] == "Beverages"

    mock_dashboard_service.get_agent_daily_report.assert_awaited_once_with(
        mock_agent_employee.id,
        datetime(2026, 7, 31, 0, 0, tzinfo=UTC),
        datetime(2026, 7, 31, 23, 59, 59, tzinfo=UTC),
    )
