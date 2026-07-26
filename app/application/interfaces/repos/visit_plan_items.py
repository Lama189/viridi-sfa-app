from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.visit_plan_items import VisitPlanItem


class IVisitPlanItemRepository(ABC):

    @abstractmethod
    async def add_many(self, items: list[VisitPlanItem]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_plan(self, visit_plan_id: UUID) -> list[VisitPlanItem]:
        raise NotImplementedError
