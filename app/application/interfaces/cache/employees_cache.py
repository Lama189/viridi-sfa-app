from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.auth import AuthenticatedEmployee


class IEmployeesCacheRepository(ABC):
    @abstractmethod
    async def get_refresh_token(self, employee_id: UUID) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def set_refresh_token(
        self,
        employee_id: UUID,
        token: str,
        expire_days: int = 30,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_refresh_token(self, employee_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def set_employee(
        self,
        employee_id: UUID,
        employee: AuthenticatedEmployee,
        expire_seconds: int = 900,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_employee(self, employee_id: UUID) -> AuthenticatedEmployee | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_employee(self, employee_id: UUID) -> None:
        raise NotImplementedError
