from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_dashboard_service
from app.application.interfaces.services.dashboard import EmployeeDashboard
from app.core.extensions import VisitPlanNotFoundError
from app.domain.entities.auth import AuthenticatedEmployee
from app.infrastructure.postgres.models.enums import EmployeeRole
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
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_get_dashboard_success(client, mock_dashboard_service, mock_agent_employee):
    mock_dashboard_service.get_employee_dashboard.return_value = EmployeeDashboard(
        total_points=25,
        completed_points=12,
        remaining_points=13,
        completion_percentage=Decimal("48"),
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
    assert data["completion_percentage"] == "48" or data["completion_percentage"] == 48 or float(data["completion_percentage"]) == 48.0
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
