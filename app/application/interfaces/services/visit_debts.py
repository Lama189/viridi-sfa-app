from abc import ABC, abstractmethod
from uuid import UUID
from decimal import Decimal

from app.domain.entities.visit_debts import VisitDebt


class IVisitDebtService(ABC):

    @abstractmethod
    async def add(
        self,
        visit_id: UUID,
        amount: Decimal,
        comment: str | None = None,
    ) -> VisitDebt:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        visit_debt_id: UUID,
        amount: Decimal,
        comment: str | None = None,
    ) -> VisitDebt:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, visit_debt_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_visit(self, visit_id: UUID) -> list[VisitDebt]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, visit_debt_id: UUID) -> VisitDebt:
        raise NotImplementedError
