from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.dto.employee_devices import RegisterDeviceDTO
from app.application.services.employee_devices import EmployeeDeviceService
from app.core.exceptions import EmployeeNotFoundError
from app.domain.entities.employee_devices import EmployeeDevice
from app.domain.entities.employees import Employee


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.employees = AsyncMock()
    uow.employee_devices = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return EmployeeDeviceService(mock_uow)


@pytest.mark.asyncio
async def test_register_device_success(service, mock_uow):
    employee_id = uuid4()
    mock_uow.employees.get_by_id.return_value = Employee(
        id=employee_id,
        phone="+998901234567",
        password_hash="hash",
        full_name="Agent Test",
    )

    dto = RegisterDeviceDTO(
        employee_id=employee_id,
        fcm_token="fcm_token_12345",
        device_type="android",
    )
    result = await service.register_device(dto)

    assert result.employee_id == employee_id
    assert result.fcm_token == "fcm_token_12345"
    assert result.device_type == "android"
    mock_uow.employee_devices.add_or_update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_device_employee_not_found(service, mock_uow):
    mock_uow.employees.get_by_id.return_value = None

    dto = RegisterDeviceDTO(
        employee_id=uuid4(),
        fcm_token="fcm_token_12345",
    )
    with pytest.raises(EmployeeNotFoundError):
        await service.register_device(dto)


@pytest.mark.asyncio
async def test_list_by_employee(service, mock_uow):
    employee_id = uuid4()
    device = EmployeeDevice(employee_id=employee_id, fcm_token="tok123")
    mock_uow.employee_devices.list_by_employee.return_value = [device]

    res = await service.list_by_employee(employee_id)
    assert len(res) == 1
    assert res[0].fcm_token == "tok123"


@pytest.mark.asyncio
async def test_remove_device(service, mock_uow):
    await service.remove_device("tok123")
    mock_uow.employee_devices.delete_by_token.assert_awaited_once_with("tok123")
    mock_uow.commit.assert_awaited_once()
