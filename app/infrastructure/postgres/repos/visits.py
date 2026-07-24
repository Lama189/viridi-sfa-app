from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.visits import IVisitRepository
from app.domain.entities.visits import Visit
from app.domain.enums import VisitStatus
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

    async def list_by_employee(self, employee_id: UUID, active: bool = True, limit: int = 1) -> list[Visit]:
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
        stmt = select(VisitModel).where(
            VisitModel.retail_point_id == retail_point_id
        )

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
