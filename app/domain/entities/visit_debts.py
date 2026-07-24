from uuid import UUID, uuid4
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, field


@dataclass(slots=True)
class VisitDebt:
    visit_id: UUID
    amount: Decimal
    comment: str | None

    id: UUID = field(default_factory=uuid4) 
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def change_amount(self, amount: Decimal) -> None:
        if amount <= 0:
            raise ValueError("Debt amount must be greater than zero.")

        self.amount = amount

    def change_comment(self, comment: str | None) -> None:
        self.comment = comment