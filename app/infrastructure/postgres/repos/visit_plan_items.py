from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.visit_plan_items import IVisitPlanItemRepository
from app.domain.entities.visit_plan_items import VisitPlanItem
from app.infrastructure.postgres.models.visit_plan_items import (
    VisitPlanItem as VisitPlanItemModel,
)


class PostgresVisitPlanItemRepository(IVisitPlanItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, items: list[VisitPlanItem]) -> None:
        models = [self._to_model(item) for item in items]
        self._session.add_all(models)
        await self._session.flush()

    async def list_by_plan(self, visit_plan_id: UUID) -> list[VisitPlanItem]:
        result = await self._session.execute(
            select(VisitPlanItemModel)
            .where(VisitPlanItemModel.visit_plan_id == visit_plan_id)
            .order_by(VisitPlanItemModel.order)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete_by_plan(self, visit_plan_id: UUID) -> None:
        await self._session.execute(
            sa_delete(VisitPlanItemModel).where(
                VisitPlanItemModel.visit_plan_id == visit_plan_id
            )
        )
        await self._session.flush()

    async def count_by_plan_id(self, plan_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count(VisitPlanItemModel.id)).where(
                VisitPlanItemModel.visit_plan_id == plan_id
            )
        )
        return result.scalar_one() or 0

    def _to_domain(self, model: VisitPlanItemModel) -> VisitPlanItem:
        return VisitPlanItem(
            id=model.id,
            visit_plan_id=model.visit_plan_id,
            retail_point_id=model.retail_point_id,
            order=model.order,
            status=model.status,
        )

    def _to_model(self, item: VisitPlanItem) -> VisitPlanItemModel:
        return VisitPlanItemModel(
            id=item.id,
            visit_plan_id=item.visit_plan_id,
            retail_point_id=item.retail_point_id,
            order=item.order,
            status=item.status,
        )
