from uuid import UUID

from app.application.dto.employee_devices import RegisterDeviceDTO
from app.application.interfaces.services.employee_devices import (
    IEmployeeDeviceService,
)
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import EmployeeNotFoundError
from app.domain.entities.employee_devices import EmployeeDevice


class EmployeeDeviceService(IEmployeeDeviceService):
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def register_device(self, dto: RegisterDeviceDTO) -> EmployeeDevice:
        employee = await self._uow.employees.get_by_id(dto.employee_id)
        if not employee:
            raise EmployeeNotFoundError()

        device = EmployeeDevice(
            employee_id=dto.employee_id,
            fcm_token=dto.fcm_token,
            device_type=dto.device_type,
        )

        await self._uow.employee_devices.add_or_update(device)
        await self._uow.commit()

        return device

    async def list_by_employee(self, employee_id: UUID) -> list[EmployeeDevice]:
        return await self._uow.employee_devices.list_by_employee(employee_id)

    async def remove_device(self, fcm_token: str) -> None:
        await self._uow.employee_devices.delete_by_token(fcm_token)
        await self._uow.commit()

    async def remove_employee_devices(self, employee_id: UUID) -> None:
        await self._uow.employee_devices.delete_by_employee(employee_id)
        await self._uow.commit()
