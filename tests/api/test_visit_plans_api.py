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
from app.domain.enums import EmployeeRole
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
async def test_generate_routes_admin_success(
    client,
    mock_routes_generator_service,
    mock_admin_employee,
):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee

    response = await client.post("/api/v1/visit-plans/generate-routes")

    assert response.status_code == 204
    mock_routes_generator_service.generate.assert_awaited_once()
