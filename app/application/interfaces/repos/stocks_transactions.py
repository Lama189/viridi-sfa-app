from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.stocks import StockTransaction


class IStockTransactionRepository(ABC):
    @abstractmethod
    async def add(self, transaction: StockTransaction) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_reference(self, reference_id: UUID) -> list[StockTransaction]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_product(self, product_id: UUID) -> list[StockTransaction]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_warehouse(self, warehouse_id: UUID) -> list[StockTransaction]:
        raise NotImplementedError
