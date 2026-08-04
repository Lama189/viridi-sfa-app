from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.visit_plans import VisitPlan


class IVisitPlanService(ABC):
    @abstractmethod
    async def create_plan(
        self,
        plan: VisitPlan,
    ) -> VisitPlan:
        raise NotImplementedError

    @abstractmethod
    async def generate_for_employee(
        self,
        employee_id: UUID,
        plan_date: date,
        overwrite: bool = True,
    ) -> VisitPlan:
        raise NotImplementedError

    @abstractmethod
    async def get_by_employee_and_date(
        self,
        employee_id: UUID,
        plan_date: date,
    ) -> VisitPlan:
        raise NotImplementedError

    @abstractmethod
    async def get_today_plan(
        self,
        employee_id: UUID,
    ) -> VisitPlan:
        raise NotImplementedError
