from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.retail_points import RetailPoint


class IRetailPointRepository(ABC):

    @abstractmethod
    async def add(self, retail_point: RetailPoint) -> None:
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