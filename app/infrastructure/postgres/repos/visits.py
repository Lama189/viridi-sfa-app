from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.application.interfaces.repos.visits import IVisitRepository
from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.visit_debts import VisitDebt
from app.domain.entities.visit_media import VisitMedia
from app.domain.entities.visits import Visit, VisitDetails
from app.domain.enums import VisitStatus
from app.infrastructure.postgres.models.visit_plan_items import (
    VisitPlanItem as VisitPlanItemModel,
)
from app.infrastructure.postgres.models.visits import Visit as VisitModel


class PostgresVisitRepository(IVisitRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, visit: Visit) -> None:
        model = self._to_model(visit)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, visit_id: UUID) -> Visit | None:
        result = await self._session.execute(
            select(VisitModel).where(VisitModel.id == visit_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_details_by_id(self, visit_id: UUID) -> VisitDetails | None:
        stmt = (
            select(VisitModel)
            .where(VisitModel.id == visit_id)
            .options(
                joinedload(VisitModel.retail_point),
                selectinload(VisitModel.created_orders),
                selectinload(VisitModel.delivered_orders),
                selectinload(VisitModel.debts),
                selectinload(VisitModel.media),
            )
        )
        result = await self._session.execute(stmt)
        model = result.unique().scalar_one_or_none()
        if model is None:
            return None
        return self._to_details_domain(model)

    async def list_by_employee(
        self, employee_id: UUID, active: bool = True, limit: int = 1
    ) -> list[Visit]:
        stmt = select(VisitModel).where(VisitModel.employee_id == employee_id)

        if active:
            stmt = stmt.where(
                VisitModel.status == VisitStatus.IN_PROGRESS,
                VisitModel.started_at.isnot(None),
                VisitModel.finished_at.is_(None),
            )

        stmt = stmt.limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_retail_point(self, retail_point_id: UUID) -> list[Visit]:
        stmt = select(VisitModel).where(VisitModel.retail_point_id == retail_point_id)

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def list(
        self,
        employee_id: UUID | None = None,
        retail_point_id: UUID | None = None,
        status: VisitStatus | None = None,
    ) -> list[Visit]:
        stmt = select(VisitModel)

        if employee_id is not None:
            stmt = stmt.where(VisitModel.employee_id == employee_id)
        if retail_point_id is not None:
            stmt = stmt.where(VisitModel.retail_point_id == retail_point_id)
        if status is not None:
            stmt = stmt.where(VisitModel.status == status)

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(VisitModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def update(self, visit: Visit) -> None:
        await self._session.execute(
            update(VisitModel)
            .where(VisitModel.id == visit.id)
            .values(
                employee_id=visit.employee_id,
                retail_point_id=visit.retail_point_id,
                status=visit.status,
                started_at=visit.started_at,
                finished_at=visit.finished_at,
            )
        )
        await self._session.flush()

    async def delete(self, visit: Visit) -> None:
        await self._session.execute(
            sa_delete(VisitModel).where(VisitModel.id == visit.id)
        )
        await self._session.flush()

    async def count_completed_by_plan(
        self,
        plan_id: UUID,
        employee_id: UUID,
    ) -> int:
        subquery = select(VisitPlanItemModel.retail_point_id).where(
            VisitPlanItemModel.visit_plan_id == plan_id
        )
        stmt = select(func.count(func.distinct(VisitModel.retail_point_id))).where(
            VisitModel.employee_id == employee_id,
            VisitModel.status == VisitStatus.COMPLETED,
            VisitModel.retail_point_id.in_(subquery),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    def _to_domain(self, model: VisitModel) -> Visit:
        return Visit(
            id=model.id,
            employee_id=model.employee_id,
            retail_point_id=model.retail_point_id,
            status=model.status,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )

    def _to_model(self, visit: Visit) -> VisitModel:
        return VisitModel(
            id=visit.id,
            employee_id=visit.employee_id,
            retail_point_id=visit.retail_point_id,
            status=visit.status,
            started_at=visit.started_at,
            finished_at=visit.finished_at,
        )

    def _to_details_domain(self, model: VisitModel) -> VisitDetails:
        visit = self._to_domain(model)
        rp_model = model.retail_point
        rp = RetailPoint(
            id=rp_model.id,
            name=rp_model.name,
            legal_name=rp_model.legal_name,
            client_type=rp_model.client_type,
            address=rp_model.address,
            landmark=rp_model.landmark,
            contact_person=rp_model.contact_person,
            phone_number=rp_model.phone_number,
            inn=rp_model.inn,
            checking_account=rp_model.checking_account,
            bank_name=rp_model.bank_name,
            mfo=rp_model.mfo,
            oked=rp_model.oked,
            latitude=rp_model.latitude,
            longitude=rp_model.longitude,
            photo_id=rp_model.photo_id,
            created_by_employee_id=rp_model.created_by_employee_id,
            is_active=rp_model.is_active,
            total_debt=getattr(rp_model, "total_debt", None) or Decimal("0.00"),
        )
        debts = [
            VisitDebt(
                id=d.id,
                visit_id=d.visit_id,
                amount=d.amount,
                comment=d.comment,
                created_at=d.created_at,
            )
            for d in (model.debts or [])
        ]
        media = [
            VisitMedia(
                id=m.id,
                visit_id=m.visit_id,
                media_id=m.media_id,
                created_at=m.created_at,
            )
            for m in (model.media or [])
        ]
        return VisitDetails(
            visit=visit,
            retail_point=rp,
            debts=debts,
            media=media,
        )
