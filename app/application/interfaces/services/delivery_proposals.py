from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.notifications import Notification
from app.domain.entities.orders import Order


class IDeliveryProposalService(ABC):
    @abstractmethod
    async def notify_order_assigned(self, order_id: UUID) -> Notification | None:
        raise NotImplementedError

    @abstractmethod
    async def plan_order_delivery(self, order_id: UUID) -> Order | None:
        raise NotImplementedError

    async def process_assembled_order(self, order_id: UUID) -> Notification | None:
        return await self.notify_order_assigned(order_id)
