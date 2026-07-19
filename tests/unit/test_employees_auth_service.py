from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.v1.schemas.employees import EmployeeLoginDTO
from app.application.services.employees import EmployeesAuthService
from app.core.extensions import UserNotFoundError, InvalidPasswordError, UserNotActiveError
from app.domain.entities.employees import Employee


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.employees = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_cache):
    return EmployeesAuthService(mock_uow, mock_cache)


# --- login ---

@pytest.mark.asyncio
@patch("app.application.services.employees.SecurityUtils.verify_password", return_value=True)
@patch("app.application.services.employees.SecurityUtils.generate_access_token", return_value="access_tok")
@patch("app.application.services.employees.SecurityUtils.generate_refresh_token", return_value="refresh_tok")
async def test_login_success(mock_refresh, mock_access, mock_verify, service, mock_uow, mock_cache):
    uid = uuid4()
    emp = Employee(phone="+998901234567", password_hash="hash", full_name="Test", id=uid, is_active=True)
    mock_uow.employees.get_by.return_value = emp

    dto = EmployeeLoginDTO(phone="+998901234567", password="secret123")
    result = await service.login(dto)

    assert result.access_token == "access_tok"
    assert result.refresh_token == "refresh_tok"
    assert result.employee.phone == "+998901234567"
    mock_cache.set_refresh_token.assert_awaited_once()
    mock_cache.set_employee.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_user_not_found(service, mock_uow):
    mock_uow.employees.get_by.return_value = None

    dto = EmployeeLoginDTO(phone="+998900000000", password="secret123")
    with pytest.raises(UserNotFoundError):
        await service.login(dto)


@pytest.mark.asyncio
@patch("app.application.services.employees.SecurityUtils.verify_password", return_value=False)
async def test_login_invalid_password(mock_verify, service, mock_uow):
    emp = Employee(phone="+998901234567", password_hash="hash", full_name="Test")
    mock_uow.employees.get_by.return_value = emp

    dto = EmployeeLoginDTO(phone="+998901234567", password="wrongpassword")
    with pytest.raises(InvalidPasswordError):
        await service.login(dto)


@pytest.mark.asyncio
@patch("app.application.services.employees.SecurityUtils.verify_password", return_value=True)
async def test_login_inactive_user(mock_verify, service, mock_uow):
    emp = Employee(phone="+998901234567", password_hash="hash", full_name="Test", is_active=False)
    mock_uow.employees.get_by.return_value = emp

    dto = EmployeeLoginDTO(phone="+998901234567", password="secret123")
    with pytest.raises(UserNotActiveError):
        await service.login(dto)


# --- refresh ---

@pytest.mark.asyncio
@patch("app.application.services.employees.SecurityUtils.verify_token")
@patch("app.application.services.employees.SecurityUtils.generate_access_token", return_value="new_access")
async def test_refresh_success(mock_access, mock_verify, service, mock_uow, mock_cache):
    uid = uuid4()
    mock_verify.return_value = {
        "sub": str(uid),
        "role": "agent",
        "phone": "+998901234567",
    }
    mock_cache.get_refresh_token.return_value = "old_refresh"

    result = await service.refresh("old_refresh")

    assert result.access_token == "new_access"
    assert result.refresh_token == "old_refresh"
    assert result.user_id == uid
    mock_cache.get_refresh_token.assert_awaited_once_with(str(uid))


@pytest.mark.asyncio
@patch("app.application.services.employees.SecurityUtils.verify_token")
async def test_refresh_invalid_token_in_cache(mock_verify, service, mock_uow, mock_cache):
    uid = uuid4()
    mock_verify.return_value = {"sub": str(uid)}
    mock_cache.get_refresh_token.return_value = None

    with pytest.raises(ValueError, match="Refresh token is invalid"):
        await service.refresh("bad_refresh")


@pytest.mark.asyncio
@patch("app.application.services.employees.SecurityUtils.verify_token")
async def test_refresh_token_mismatch(mock_verify, service, mock_uow, mock_cache):
    uid = uuid4()
    mock_verify.return_value = {"sub": str(uid)}
    mock_cache.get_refresh_token.return_value = "stored_token"

    with pytest.raises(ValueError, match="Refresh token is invalid"):
        await service.refresh("different_token")


# --- logout ---

@pytest.mark.asyncio
async def test_logout(service, mock_cache):
    await service.logout("emp-123")

    mock_cache.delete_refresh_token.assert_awaited_once_with("emp-123")
    mock_cache.delete_employee.assert_awaited_once_with("emp-123")
