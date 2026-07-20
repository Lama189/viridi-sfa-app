from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.orders import OrderItem


class IOrderItemRepository(ABC):

    @abstractmethod
    async def add(self, item: OrderItem) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_order(self, order_id: UUID) -> list[OrderItem]:
        raise NotImplementedError

    @abstractmethod
    async def delete_by_order(self, order_id: UUID) -> None:
        raise NotImplementedError