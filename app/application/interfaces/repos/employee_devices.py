from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.employee_devices import EmployeeDevice


class IEmployeeDeviceRepository(ABC):
    @abstractmethod
    async def add_or_update(self, device: EmployeeDevice) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_employee(self, employee_id: UUID) -> list[EmployeeDevice]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_token(self, fcm_token: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_tokens(self, tokens: list[str]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_employee(self, employee_id: UUID) -> None:
        raise NotImplementedError
