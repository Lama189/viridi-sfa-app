from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.stocks import Stock


class IStockRepository(ABC):
    @abstractmethod
    async def add(self, stock: Stock) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get(self, warehouse_id: UUID, product_id: UUID) -> Stock | None:
        raise NotImplementedError

    @abstractmethod
    async def get_for_update(
        self, warehouse_id: UUID, product_id: UUID
    ) -> Stock | None:
        raise NotImplementedError

    @abstractmethod
    async def get_many_for_update(
        self,
        warehouse_id: UUID,
        product_ids: list[UUID],
    ) -> list[Stock]:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_by_warehouse(self, warehouse_id: UUID) -> list[Stock]:
        raise NotImplementedError

    @abstractmethod
    async def get_stocks_by_warehouse(self, warehouse_id: UUID) -> list:
        raise NotImplementedError

    @abstractmethod
    async def update(self, stock: Stock) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, stock: Stock) -> None:
        raise NotImplementedError
