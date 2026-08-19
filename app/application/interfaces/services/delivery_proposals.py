from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.notifications import Notification


class IDeliveryProposalService(ABC):
    @abstractmethod
    async def process_assembled_order(self, order_id: UUID) -> Notification | None:
        raise NotImplementedError
