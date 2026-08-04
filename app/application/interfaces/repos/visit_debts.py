from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.domain.entities.visit_debts import VisitDebt


class IVisitDebtRepository(ABC):
    @abstractmethod
    async def add(self, visit_debt: VisitDebt) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, visit_debt_id: UUID) -> VisitDebt | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_visit(self, visit_id: UUID) -> list[VisitDebt]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, visit_debt: VisitDebt) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, visit_debt: VisitDebt) -> None:
        raise NotImplementedError

    @abstractmethod
    async def count_by_employee_and_date(
        self,
        employee_id: UUID,
        target_date: date,
    ) -> int:
        raise NotImplementedError
