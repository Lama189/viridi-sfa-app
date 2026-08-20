from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.orders import Order
from app.domain.entities.visit_plans import VisitPlan


class IDeliveryAssignmentService(ABC):
    @abstractmethod
    async def assign_order_to_next_visit(self, order: Order) -> VisitPlan | None:
        raise NotImplementedError

    async def assign_order(self, order: Order) -> VisitPlan | None:
        return await self.assign_order_to_next_visit(order)

    async def assign_order_by_id(self, order_id: UUID) -> VisitPlan | None:
        raise NotImplementedError
