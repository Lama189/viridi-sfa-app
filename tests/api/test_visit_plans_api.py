from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_current_user,
    get_routes_generator_service,
    get_visit_plans_service,
)
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.enums import EmployeeRole, RouteGenerationStart
from app.main import app


@pytest.fixture
def mock_visit_plans_service():

    return AsyncMock()


@pytest.fixture
def mock_routes_generator_service():
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


@pytest.fixture
def mock_agent_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000001",
        role=EmployeeRole.AGENT,
        full_name="Mock Agent",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_visit_plans_service, mock_routes_generator_service):
    app.dependency_overrides[get_visit_plans_service] = lambda: mock_visit_plans_service
    app.dependency_overrides[get_routes_generator_service] = lambda: (
        mock_routes_generator_service
    )
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_clear_routes_admin_success(
    client,
    mock_routes_generator_service,
    mock_admin_employee,
):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee

    response = await client.post("/api/v1/visit-plans/clear-routes")

    assert response.status_code == 204
    mock_routes_generator_service.clear_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_routes_forbidden_for_agent(
    client,
    mock_routes_generator_service,
    mock_agent_employee,
):
    app.dependency_overrides[get_current_user] = lambda: mock_agent_employee

    response = await client.post("/api/v1/visit-plans/clear-routes")

    assert response.status_code == 403
    mock_routes_generator_service.clear_all.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_routes_admin_default(
    client,
    mock_routes_generator_service,
    mock_admin_employee,
):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee

    response = await client.post("/api/v1/visit-plans/generate-routes")

    assert response.status_code == 204
    mock_routes_generator_service.generate.assert_awaited_once_with(
        start=RouteGenerationStart.NEXT_WEEK
    )


@pytest.mark.asyncio
async def test_generate_routes_admin_from_today(
    client,
    mock_routes_generator_service,
    mock_admin_employee,
):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee

    response = await client.post("/api/v1/visit-plans/generate-routes?from=today")

    assert response.status_code == 204
    mock_routes_generator_service.generate.assert_awaited_once_with(
        start=RouteGenerationStart.TODAY
    )


@pytest.mark.asyncio
async def test_generate_routes_admin_start_tomorrow(
    client,
    mock_routes_generator_service,
    mock_admin_employee,
):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee

    response = await client.post("/api/v1/visit-plans/generate-routes?start=tomorrow")

    assert response.status_code == 204
    mock_routes_generator_service.generate.assert_awaited_once_with(
        start=RouteGenerationStart.TOMORROW
    )


@pytest.mark.asyncio
async def test_get_today_plan_api(
    client,
    mock_visit_plans_service,
    mock_agent_employee,
):
    from datetime import date

    from app.application.dto.visit_plans import VisitPlanDTO
    from app.domain.enums import VisitPlanStatus, Weekday

    app.dependency_overrides[get_current_user] = lambda: mock_agent_employee
    plan_dto = VisitPlanDTO(
        id=uuid4(),
        employee_id=mock_agent_employee.id,
        date=date.today(),
        weekday=Weekday.MONDAY,
        status=VisitPlanStatus.PLANNED,
        items=[],
    )
    mock_visit_plans_service.get_today_plan_dto.return_value = plan_dto

    response = await client.get("/api/v1/visit-plans/today")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(plan_dto.id)
    assert data["employee_id"] == str(mock_agent_employee.id)
    mock_visit_plans_service.get_today_plan_dto.assert_awaited_once_with(
        mock_agent_employee.id
    )


@pytest.mark.asyncio
async def test_get_plan_by_date_api(
    client,
    mock_visit_plans_service,
    mock_agent_employee,
):
    from datetime import date

    from app.application.dto.visit_plans import VisitPlanDTO
    from app.domain.enums import VisitPlanStatus, Weekday

    app.dependency_overrides[get_current_user] = lambda: mock_agent_employee
    target_date = date(2026, 8, 26)
    plan_dto = VisitPlanDTO(
        id=uuid4(),
        employee_id=mock_agent_employee.id,
        date=target_date,
        weekday=Weekday.WEDNESDAY,
        status=VisitPlanStatus.PLANNED,
        items=[],
    )
    mock_visit_plans_service.get_plan_by_date_dto.return_value = plan_dto

    response = await client.get(f"/api/v1/visit-plans/{target_date}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(plan_dto.id)
    mock_visit_plans_service.get_plan_by_date_dto.assert_awaited_once_with(
        mock_agent_employee.id, target_date
    )


@pytest.mark.asyncio
async def test_generate_visit_plan_api(
    client,
    mock_visit_plans_service,
    mock_admin_employee,
):
    from datetime import date

    from app.application.dto.visit_plans import VisitPlanDTO
    from app.domain.enums import VisitPlanStatus, Weekday

    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    target_date = date(2026, 8, 27)
    emp_id = uuid4()
    plan_dto = VisitPlanDTO(
        id=uuid4(),
        employee_id=emp_id,
        date=target_date,
        weekday=Weekday.THURSDAY,
        status=VisitPlanStatus.PLANNED,
        items=[],
    )
    mock_visit_plans_service.generate_for_employee_dto.return_value = plan_dto

    response = await client.post(
        "/api/v1/visit-plans/generate",
        json={"employee_id": str(emp_id), "plan_date": "2026-08-27"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(plan_dto.id)
    mock_visit_plans_service.generate_for_employee_dto.assert_awaited_once_with(
        emp_id, target_date
    )
