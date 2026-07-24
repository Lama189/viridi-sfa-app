from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.visits import Visit


class IVisitRepository(ABC):

    @abstractmethod
    async def add(self, visit: Visit) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, visit_id: UUID) -> Visit | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_employee(self, employee_id: UUID, active: bool = True) -> list[Visit]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_retail_point(self, retail_point_id: UUID) -> list[Visit]:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def update(self, visit: Visit) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, visit: Visit) -> None:
        raise NotImplementedError
