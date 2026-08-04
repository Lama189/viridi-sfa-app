from abc import ABC, abstractmethod

from app.application.dto.stocks import (
    StockBatchOperationDTO,
    StockCreateDTO,
    StockOperationDTO,
)
from app.domain.entities.stocks import Stock


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
