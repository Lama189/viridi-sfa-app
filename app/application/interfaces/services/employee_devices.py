from abc import ABC, abstractmethod
from uuid import UUID

from app.application.dto.employee_devices import RegisterDeviceDTO
from app.domain.entities.employee_devices import EmployeeDevice


class IEmployeeDeviceService(ABC):
    @abstractmethod
    async def register_device(self, dto: RegisterDeviceDTO) -> EmployeeDevice:
        raise NotImplementedError

    @abstractmethod
    async def list_by_employee(self, employee_id: UUID) -> list[EmployeeDevice]:
        raise NotImplementedError

    @abstractmethod
    async def remove_device(self, fcm_token: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_employee_devices(self, employee_id: UUID) -> None:
        raise NotImplementedError
