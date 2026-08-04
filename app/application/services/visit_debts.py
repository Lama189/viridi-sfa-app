from decimal import Decimal
from uuid import UUID

from app.application.interfaces.services.visit_debts import IVisitDebtService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import VisitDebtNotFoundError
from app.domain.entities.visit_debts import VisitDebt


class VisitDebtService(IVisitDebtService):
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def add(
        self, visit_id: UUID, amount: Decimal, comment: str | None = None
    ) -> VisitDebt:
        debt = VisitDebt(visit_id, amount, comment)
        await self._uow.visit_debts.add(debt)

        return debt

    async def update(
        self, visit_debt_id: UUID, amount: Decimal, comment: str | None = None
    ) -> VisitDebt:
        visit_debt = await self._uow.visit_debts.get_by_id(visit_debt_id)
        if not visit_debt:
            raise VisitDebtNotFoundError()

        visit_debt.change_amount(amount)
        visit_debt.change_comment(comment)

        await self._uow.visit_debts.update(visit_debt)

        return visit_debt

    async def delete(self, visit_debt_id: UUID) -> None:
        visit_debt = await self._uow.visit_debts.get_by_id(visit_debt_id)
        if not visit_debt:
            raise VisitDebtNotFoundError()

        await self._uow.visit_debts.delete(visit_debt)

    async def list_by_visit(self, visit_id: UUID) -> list[VisitDebt]:
        return await self._uow.visit_debts.list_by_visit(visit_id)

    async def get_by_id(self, visit_debt_id: UUID) -> VisitDebt:
        debt = await self._uow.visit_debts.get_by_id(visit_debt_id)
        if not debt:
            raise VisitDebtNotFoundError()

        return debt
