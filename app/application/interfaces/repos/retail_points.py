from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.retail_points import RetailPoint, RetailPointIdentity
from app.domain.enums import Weekday


class IRetailPointRepository(ABC):

    @abstractmethod
    async def add(self, retail_point: RetailPoint) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_many(self, retail_points: list[RetailPoint]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def find_existing_by_identity(
        self,
        identities: list[RetailPointIdentity],
    ) -> dict[RetailPointIdentity, UUID]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, category_id: UUID) -> RetailPoint | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, only_active: bool = True) -> list[RetailPoint]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, category: RetailPoint) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, category: RetailPoint) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_employee(
        self,
        employee_id: UUID,
        only_active: bool = True,
    ) -> list[RetailPoint]:
        raise NotImplementedError

    @abstractmethod
    async def list_paginated(
        self,
        employee_id: UUID,
        limit: int,
        offset: int,
    ) -> list[RetailPoint]:
        raise NotImplementedError