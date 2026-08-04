from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.visit_plans import IVisitPlanRepository
from app.domain.entities.visit_plans import VisitPlan
from app.infrastructure.postgres.models.visit_plans import VisitPlan as VisitPlanModel


class PostgresVisitPlanRepository(IVisitPlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, visit_plan: VisitPlan) -> None:
        model = self._to_model(visit_plan)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, visit_plan_id: UUID) -> VisitPlan | None:
        result = await self._session.execute(
            select(VisitPlanModel).where(VisitPlanModel.id == visit_plan_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_employee_and_date(
        self,
        employee_id: UUID,
        plan_date: date,
    ) -> VisitPlan | None:
        result = await self._session.execute(
            select(VisitPlanModel).where(
                VisitPlanModel.employee_id == employee_id,
                VisitPlanModel.plan_date == plan_date,
            )
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_employee(self, employee_id: UUID) -> list[VisitPlan]:
        result = await self._session.execute(
            select(VisitPlanModel).where(VisitPlanModel.employee_id == employee_id)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: VisitPlanModel) -> VisitPlan:
        return VisitPlan(
            id=model.id,
            employee_id=model.employee_id,
            plan_date=model.plan_date,
            status=model.status,
        )

    def _to_model(self, visit_plan: VisitPlan) -> VisitPlanModel:
        return VisitPlanModel(
            id=visit_plan.id,
            employee_id=visit_plan.employee_id,
            plan_date=visit_plan.plan_date,
            status=visit_plan.status,
        )
