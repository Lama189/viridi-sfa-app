from uuid import UUID
from abc import ABC, abstractmethod

from app.domain.entities.inventory import Product


class IProductRepository(ABC):

    @abstractmethod
    async def add(self, product: Product) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, product_id: UUID) -> Product | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_by_ids(self, product_ids: list[UUID]) -> list[Product]:
        raise NotImplementedError
    
    @abstractmethod
    async def list_all(self, only_active: bool = True) -> list[Product]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, product: Product) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, product: Product) -> None:
        raise NotImplementedError