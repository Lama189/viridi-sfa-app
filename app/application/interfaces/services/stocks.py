from abc import ABC, abstractmethod

from app.api.v1.schemas.stocks import (
    StockCreateRequest,
    StockOperationRequest,
)
from app.domain.entities.stocks import Stock


class IStockService(ABC):

    @abstractmethod
    async def create_stock(self, dto: StockCreateRequest) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def add_stock(self, dto: StockOperationRequest) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def reserve_stock(self, dto: StockOperationRequest) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def release_reservation(self, dto: StockOperationRequest) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def confirm_sale(self, dto: StockOperationRequest) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def write_off(self, dto: StockOperationRequest) -> Stock:
        raise NotImplementedError

    @abstractmethod
    async def return_stock(self, dto: StockOperationRequest) -> Stock:
        raise NotImplementedError