from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.retail_point_assignments import RetailPointAssignment


class IRetailPointAssignmentService(ABC):

    @abstractmethod
    async def create(
        self, retail_point_id: UUID,
    ) -> RetailPointAssignment:
        raise NotImplementedError

    @abstractmethod
    async def create_many(
        self,
        retail_point_ids: list[UUID]
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, retail_point_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def assign_employee(
        self, retail_point_id: UUID, employee_id: UUID,
    ) -> RetailPointAssignment:
        raise NotImplementedError

    @abstractmethod
    async def unassign_employee(
        self, retail_point_id: UUID,
    ) -> RetailPointAssignment:
        raise NotImplementedError
    
    
