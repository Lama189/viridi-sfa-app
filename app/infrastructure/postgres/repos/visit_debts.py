from datetime import date
from uuid import UUID

from sqlalchemy import select, func, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.visit_debts import IVisitDebtRepository
from app.domain.entities.visit_debts import VisitDebt
from app.infrastructure.postgres.models.visit_debts import VisitDebt as VisitDebtModel
from app.infrastructure.postgres.models.visits import Visit as VisitModel


class PostgresVisitDebtRepository(IVisitDebtRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, visit_debt: VisitDebt) -> None:
        model = self._to_model(visit_debt)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, visit_debt_id: UUID) -> VisitDebt | None:
        result = await self._session.execute(
            select(VisitDebtModel).where(VisitDebtModel.id == visit_debt_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_visit(self, visit_id: UUID) -> list[VisitDebt]:
        stmt = select(VisitDebtModel).where(
            VisitDebtModel.visit_id == visit_id
        )

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, visit_debt: VisitDebt) -> None:
        await self._session.execute(
            update(VisitDebtModel)
            .where(VisitDebtModel.id == visit_debt.id)
            .values(
                amount=visit_debt.amount,
                comment=visit_debt.comment,
            )
        )
        await self._session.flush()

    async def delete(self, visit_debt: VisitDebt) -> None:
        await self._session.execute(
            sa_delete(VisitDebtModel).where(VisitDebtModel.id == visit_debt.id)
        )
        await self._session.flush()

    async def count_by_employee_and_date(
        self,
        employee_id: UUID,
        target_date: date,
    ) -> int:
        stmt = (
            select(func.count(VisitDebtModel.id))
            .select_from(VisitDebtModel)
            .join(VisitModel, VisitDebtModel.visit_id == VisitModel.id)
            .where(
                VisitModel.employee_id == employee_id,
                func.date(VisitModel.started_at) == target_date,
            )
        )

        result = await self._session.execute(stmt)
        return result.scalar_one() or 0


    def _to_domain(self, model: VisitDebtModel) -> VisitDebt:
        return VisitDebt(
            id=model.id,
            visit_id=model.visit_id,
            amount=model.amount,
            comment=model.comment,
            created_at=model.created_at,
        )

    def _to_model(self, visit_debt: VisitDebt) -> VisitDebtModel:
        return VisitDebtModel(
            id=visit_debt.id,
            visit_id=visit_debt.visit_id,
            amount=visit_debt.amount,
            comment=visit_debt.comment,
        )
