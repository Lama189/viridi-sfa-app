from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_current_user,
    get_employees_auth_service,
    get_employees_service,
)
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.employees import Employee
from app.domain.enums import EmployeeRole
from app.main import app


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def mock_auth_service():
    return AsyncMock()


@pytest.fixture
def mock_admin_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998974227694",
        role=EmployeeRole.ADMIN,
        full_name="Mock Admin",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_service, mock_auth_service, mock_admin_employee):
    app.dependency_overrides[get_employees_service] = lambda: mock_service
    app.dependency_overrides[get_employees_auth_service] = lambda: mock_auth_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# --- POST /api/v1/employees/register ---


@pytest.mark.asyncio
async def test_register_success(client, mock_service):
    uid = uuid4()
    mock_service.create_employee.return_value = Employee(
        phone="+998901234567",
        password_hash="h",
        full_name="Test",
        id=uid,
        is_active=False,
    )

    resp = await client.post(
        "/api/v1/employees/register",
        json={
            "phone": "+998901234567",
            "password": "secret123",
            "full_name": "Test",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["phone"] == "+998901234567"


@pytest.mark.asyncio
async def test_register_duplicate(client, mock_service):
    mock_service.create_employee.side_effect = ValueError("already exists")

    resp = await client.post(
        "/api/v1/employees/register",
        json={
            "phone": "+998901234567",
            "password": "secret123",
            "full_name": "Dup",
        },
    )
    assert resp.status_code == 400


# --- POST /api/v1/employees/login ---


@pytest.mark.asyncio
async def test_login_success(client, mock_auth_service):
    uid = uuid4()
    from app.api.v1.schemas.employees import (
        EmployeeResponse,
        EmployeeWithTokensResponse,
    )

    mock_auth_service.login.return_value = EmployeeWithTokensResponse(
        access_token="acc",
        refresh_token="ref",
        employee=EmployeeResponse(
            id=uid,
            phone="+998901234567",
            full_name="Test",
            role=EmployeeRole.AGENT,
            is_active=True,
        ),
    )

    resp = await client.post(
        "/api/v1/employees/login",
        json={
            "phone": "+998901234567",
            "password": "secret123",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "acc"
    assert data["employee"]["phone"] == "+998901234567"


@pytest.mark.asyncio
async def test_login_not_found(client, mock_auth_service):
    from app.core.exceptions import UserNotFoundError

    mock_auth_service.login.side_effect = UserNotFoundError()

    resp = await client.post(
        "/api/v1/employees/login",
        json={
            "phone": "+998900000000",
            "password": "secret123",
        },
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_login_invalid_password(client, mock_auth_service):
    from app.core.exceptions import InvalidPasswordError

    mock_auth_service.login.side_effect = InvalidPasswordError()

    resp = await client.post(
        "/api/v1/employees/login",
        json={
            "phone": "+998901234567",
            "password": "wrongpassword",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_account(client, mock_auth_service):
    from app.core.exceptions import UserNotActiveError

    mock_auth_service.login.side_effect = UserNotActiveError()

    resp = await client.post(
        "/api/v1/employees/login",
        json={
            "phone": "+998901234567",
            "password": "secret123",
        },
    )
    assert resp.status_code == 403


# --- PATCH /api/v1/employees/{id} ---


@pytest.mark.asyncio
async def test_update_employee_success(client, mock_service):
    uid = uuid4()
    mock_service.update_employee.return_value = Employee(
        phone="+998901234567",
        password_hash="h",
        full_name="New",
        id=uid,
        is_active=True,
    )

    resp = await client.patch(f"/api/v1/employees/{uid}", json={"full_name": "New"})
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "New"


@pytest.mark.asyncio
async def test_update_employee_not_found(client, mock_service):
    mock_service.update_employee.side_effect = ValueError("not found")

    resp = await client.patch(f"/api/v1/employees/{uuid4()}", json={"full_name": "X"})
    assert resp.status_code == 400


# --- DELETE /api/v1/employees/{id} ---


@pytest.mark.asyncio
async def test_delete_employee_success(client, mock_service):
    resp = await client.delete(f"/api/v1/employees/{uuid4()}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_employee_not_found(client, mock_service):
    mock_service.delete_employee.side_effect = ValueError("not found")

    resp = await client.delete(f"/api/v1/employees/{uuid4()}")
    assert resp.status_code == 404
