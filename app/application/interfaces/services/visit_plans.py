from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.application.dto.visit_plans import VisitPlanDTO
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

    @abstractmethod
    async def get_today_plan_dto(
        self,
        employee_id: UUID,
    ) -> VisitPlanDTO:
        raise NotImplementedError

    @abstractmethod
    async def get_plan_by_date_dto(
        self,
        employee_id: UUID,
        plan_date: date,
    ) -> VisitPlanDTO:
        raise NotImplementedError

    @abstractmethod
    async def generate_for_employee_dto(
        self,
        employee_id: UUID,
        plan_date: date,
        overwrite: bool = True,
    ) -> VisitPlanDTO:
        raise NotImplementedError
