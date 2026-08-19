from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.visit_plans import VisitPlan


class IVisitPlanRepository(ABC):
    @abstractmethod
    async def add(self, visit_plan: VisitPlan) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, visit_plan_id: UUID) -> VisitPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_employee_and_date(
        self,
        employee_id: UUID,
        plan_date: date,
    ) -> VisitPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_employee(self, employee_id: UUID) -> list[VisitPlan]:
        raise NotImplementedError

    @abstractmethod
    async def find_next_plan_for_retail_point(
        self,
        employee_id: UUID,
        retail_point_id: UUID,
        from_date: date,
    ) -> VisitPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_all(self) -> None:
        raise NotImplementedError
