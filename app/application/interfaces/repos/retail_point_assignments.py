from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.retail_point_assignments import RetailPointAssignment


class IRetailPointAssignmentRepository(ABC):

    @abstractmethod
    async def add(self, assignment: RetailPointAssignment) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_many(self, assignments: list[RetailPointAssignment]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, assignment_id: UUID) -> RetailPointAssignment | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_retail_point_id(
        self, retail_point_id: UUID,
    ) -> RetailPointAssignment | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_employee_id(
        self, employee_id: UUID,
    ) -> list[RetailPointAssignment]:
        raise NotImplementedError

    @abstractmethod
    async def exists_by_retail_point_id(self, retail_point_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def update(self, assignment: RetailPointAssignment) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, assignment: RetailPointAssignment) -> None:
        raise NotImplementedError

    @abstractmethod
    async def clear_employee_assignments(
        self,
        retail_point_ids: list[UUID],
    ) -> None:
        raise NotImplementedError
