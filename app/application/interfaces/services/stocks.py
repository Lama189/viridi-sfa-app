from abc import ABC, abstractmethod
from uuid import UUID

from app.api.v1.schemas.inventory import ProductWithStockResponse
from app.application.dto.stocks import (
    StockBatchOperationDTO,
    StockCreateDTO,
    StockOperationDTO,
)
from app.domain.entities.stocks import Stock, StockTransaction


class IStockService(ABC):
    @abstractmethod
    async def create_stock(self, dto: StockCreateDTO) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def add_stock(self, dto: StockOperationDTO) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def reserve_stock(self, dto: StockOperationDTO) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def reserve_stocks_batch(self, dto: StockBatchOperationDTO) -> list[Stock]:
        raise NotImplementedError

    @abstractmethod
    async def release_reservation(self, dto: StockOperationDTO) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def release_reservations_batch(
        self, dto: StockBatchOperationDTO
    ) -> list[Stock]:
        raise NotImplementedError

    @abstractmethod
    async def confirm_sale(self, dto: StockOperationDTO) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def confirm_sales_batch(self, dto: StockBatchOperationDTO) -> list[Stock]:
        raise NotImplementedError

    @abstractmethod
    async def write_off(self, dto: StockOperationDTO) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def return_stock(self, dto: StockOperationDTO) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def list_transactions(
        self,
        warehouse_id: UUID | None = None,
        product_id: UUID | None = None,
        reference_id: UUID | None = None,
    ) -> list[StockTransaction]:
        raise NotImplementedError

    @abstractmethod
    async def adjust_stock(
        self,
        warehouse_id: UUID,
        product_id: UUID,
        new_quantity: int,
        actor_id: UUID | None = None,
        reference_id: UUID | None = None,
    ) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def get_warehouse_inventory(
        self, warehouse_id: UUID
    ) -> list[ProductWithStockResponse]:
        raise NotImplementedError
