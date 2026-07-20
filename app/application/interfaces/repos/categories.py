from uuid import UUID
from abc import ABC, abstractmethod

from app.domain.entities.inventory import Category


class ICategoryRepository(ABC):

    @abstractmethod
    async def add(self, category: Category) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, category_id: UUID) -> Category | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, only_active: bool = True) -> list[Category]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, category: Category) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, category: Category) -> None:
        raise NotImplementedError
