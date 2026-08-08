from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.v1.schemas.employees import EmployeeCreate, EmployeeUpdate
from app.application.services.employees import EmployeesService
from app.domain.entities.employees import Employee
from app.domain.enums import EmployeeRole


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.employees = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return EmployeesService(mock_uow)


# --- create_employee ---


@pytest.mark.asyncio
@patch(
    "app.application.services.employees.SecurityUtils.hash_password",
    return_value="hashed_value",
)
async def test_create_employee_success(mock_hash, service, mock_uow):
    mock_uow.employees.exists_by.return_value = False

    dto = EmployeeCreate(
        phone="+998901234567", password="secret123", full_name="Test Employee"
    )
    result = await service.create_employee(dto)

    assert result.phone == "+998901234567"
    assert result.full_name == "Test Employee"
    assert result.password_hash == "hashed_value"
    assert result.role == EmployeeRole.AGENT
    assert result.is_active is False
    mock_uow.employees.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch(
    "app.application.services.employees.SecurityUtils.hash_password",
    return_value="hashed_value",
)
async def test_create_employee_with_role(mock_hash, service, mock_uow):
    mock_uow.employees.exists_by.return_value = False

    dto = EmployeeCreate(
        phone="+998901234568",
        password="secret123",
        full_name="Admin",
        role=EmployeeRole.ADMIN,
    )
    result = await service.create_employee(dto)

    assert result.role == EmployeeRole.ADMIN


@pytest.mark.asyncio
async def test_create_employee_duplicate_phone(service, mock_uow):
    mock_uow.employees.exists_by.return_value = True

    dto = EmployeeCreate(phone="+998901234567", password="secret123", full_name="Dup")
    with pytest.raises(ValueError, match="already exists"):
        await service.create_employee(dto)

    mock_uow.employees.add.assert_not_awaited()


# --- get_employee ---


@pytest.mark.asyncio
async def test_get_employee_found(service, mock_uow):
    uid = uuid4()
    mock_uow.employees.get_by_id.return_value = Employee(
        phone="+998901234567",
        password_hash="h",
        full_name="X",
        id=uid,
    )

    result = await service.get_employee(uid)
    assert result is not None
    assert result.full_name == "X"


@pytest.mark.asyncio
async def test_get_employee_not_found(service, mock_uow):
    mock_uow.employees.get_by_id.return_value = None

    result = await service.get_employee(uuid4())
    assert result is None


# --- get_employee_by ---


@pytest.mark.asyncio
async def test_get_employee_by(service, mock_uow):
    mock_uow.employees.get_by.return_value = Employee(
        phone="+998901234567",
        password_hash="h",
        full_name="Y",
    )

    result = await service.get_employee_by(phone="+998901234567")
    assert result is not None
    mock_uow.employees.get_by.assert_awaited_once_with(phone="+998901234567")


# --- list_employees ---


@pytest.mark.asyncio
async def test_list_employees(service, mock_uow):
    mock_uow.employees.list_by.return_value = [
        Employee(phone="+998901111111", password_hash="h", full_name="A"),
        Employee(phone="+998902222222", password_hash="h", full_name="B"),
    ]

    result = await service.list_employees(role="agent")
    assert len(result) == 2
    mock_uow.employees.list_by.assert_awaited_once_with(role="agent")


# --- update_employee ---


@pytest.mark.asyncio
async def test_update_employee_success(service, mock_uow):
    uid = uuid4()
    emp = Employee(phone="+998905000000", password_hash="old", full_name="Old", id=uid)
    mock_uow.employees.get_by_id.return_value = emp
    mock_uow.employees.get_by.return_value = None

    dto = EmployeeUpdate(full_name="New")
    result = await service.update_employee(uid, dto)

    assert result.full_name == "New"
    mock_uow.employees.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_employee_phone_conflict(service, mock_uow):
    uid = uuid4()
    other_id = uuid4()
    emp = Employee(phone="+998905000000", password_hash="h", full_name="X", id=uid)
    mock_uow.employees.get_by_id.return_value = emp
    mock_uow.employees.get_by.return_value = Employee(
        phone="+998909999999",
        password_hash="h",
        full_name="Y",
        id=other_id,
    )

    dto = EmployeeUpdate(phone="+998909999999")
    with pytest.raises(ValueError, match="already in use"):
        await service.update_employee(uid, dto)


@pytest.mark.asyncio
async def test_update_employee_role(service, mock_uow):
    uid = uuid4()
    emp = Employee(phone="+998905000000", password_hash="h", full_name="X", id=uid)
    mock_uow.employees.get_by_id.return_value = emp
    mock_uow.employees.get_by.return_value = None

    dto = EmployeeUpdate(role=EmployeeRole.ADMIN)
    result = await service.update_employee(uid, dto)

    assert result.role == EmployeeRole.ADMIN


@pytest.mark.asyncio
async def test_update_employee_not_found(service, mock_uow):
    mock_uow.employees.get_by_id.return_value = None

    dto = EmployeeUpdate(full_name="X")
    with pytest.raises(ValueError, match="not found"):
        await service.update_employee(uuid4(), dto)


# --- delete_employee ---


@pytest.mark.asyncio
async def test_delete_employee_success(service, mock_uow):
    uid = uuid4()
    mock_uow.employees.get_by_id.return_value = Employee(
        phone="+998906000000",
        password_hash="h",
        full_name="Del",
        id=uid,
    )

    await service.delete_employee(uid)

    mock_uow.employees.delete.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_employee_not_found(service, mock_uow):
    mock_uow.employees.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await service.delete_employee(uuid4())

    mock_uow.employees.delete.assert_not_awaited()
