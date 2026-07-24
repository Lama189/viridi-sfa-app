from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True)
class VisitDebt:
    id: UUID | None
    visit_id: UUID
    amount: Decimal
    comment: str | None
    created_at: datetime | None = None

    def change_amount(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("Debt amount must be greater than zero.")

        self.amount = amount

    def change_comment(self, comment: str | None) -> None:
        self.comment = comment