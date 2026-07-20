from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.enums import StockTransactionType, TransactionActorType, StockReferenceType


from datetime import timezone


@dataclass(slots=True)
class Stock:
    warehouse_id: UUID
    product_id: UUID
    quantity: int = 0
    reserved_quantity: int = 0
    updated_at: datetime = datetime.now(timezone.utc)

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")

        if self.reserved_quantity < 0:
            raise ValueError("Reserved quantity cannot be negative")

        if self.reserved_quantity > self.quantity:
            raise ValueError(
                "Reserved quantity cannot exceed quantity"
            )

    @property
    def available_quantity(self) -> int:
        return self.quantity - self.reserved_quantity

    def increase(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self.quantity += amount
        self._touch()

    def reserve(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.available_quantity < amount:
            raise ValueError("Insufficient stock")

        self.reserved_quantity += amount
        self._touch()

    def release_reservation(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.reserved_quantity < amount:
            raise ValueError("Insufficient reservation")

        self.reserved_quantity -= amount
        self._touch()

    def sell(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.reserved_quantity < amount:
            raise ValueError("Insufficient reservation")

        self.quantity -= amount
        self.reserved_quantity -= amount
        self._touch()

    def write_off(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.available_quantity < amount:
            raise ValueError("Insufficient stock")

        self.quantity -= amount
        self._touch()

    def return_product(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self.quantity += amount
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)


@dataclass(slots=True)
class StockTransaction:
    warehouse_id: UUID
    product_id: UUID
    quantity_delta: int
    transaction_type: StockTransactionType
    reference_type: StockReferenceType
    reference_id: UUID
    id: UUID = field(default_factory=uuid4)
    actor_type: TransactionActorType = TransactionActorType.SYSTEM
    created_by_id: UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
