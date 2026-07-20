from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.employees import Employee


class IEmployeeRepository(ABC):

    @abstractmethod
    async def add(self, employee: Employee) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, employee_id: UUID) -> Employee | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by(self, **kwargs) -> Employee | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by(self, **kwargs) -> list[Employee]:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def update(self, employee: Employee) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, employee: Employee) -> None:
        raise NotImplementedError