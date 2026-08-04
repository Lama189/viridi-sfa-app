from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.exceptions import (
    InsufficientReservationError,
    InsufficientReservedStockError,
    InsufficientStockError,
)
from app.domain.enums import (
    StockReferenceType,
    StockTransactionType,
    TransactionActorType,
)


@dataclass(slots=True)
class Stock:
    warehouse_id: UUID
    product_id: UUID
    quantity: int = 0
    reserved_quantity: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")

        if self.reserved_quantity < 0:
            raise ValueError("Reserved quantity cannot be negative")

        if self.reserved_quantity > self.quantity:
            raise ValueError("Reserved quantity cannot exceed quantity")

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
            raise InsufficientStockError(
                f"Insufficient stock: available={self.available_quantity}, required={amount}"
            )

        self.reserved_quantity += amount
        self._touch()

    def release_reservation(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.reserved_quantity < amount:
            raise InsufficientReservedStockError(
                f"Insufficient reserved stock: reserved={self.reserved_quantity}, requested_release={amount}"
            )

        self.reserved_quantity -= amount
        self._touch()

    def sell(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.reserved_quantity < amount:
            raise InsufficientReservationError(
                f"Insufficient reservation for sale: reserved={self.reserved_quantity}, required={amount}"
            )

        self.quantity -= amount
        self.reserved_quantity -= amount
        self._touch()

    def write_off(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        if self.available_quantity < amount:
            raise InsufficientStockError(
                f"Insufficient stock for write-off: available={self.available_quantity}, required={amount}"
            )

        self.quantity -= amount
        self._touch()

    def return_product(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError("Amount must be positive")

        self.quantity += amount
        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)


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
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
