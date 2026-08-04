from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.enums import OrderStatus


@dataclass(slots=True)
class OrderItem:
    order_id: UUID
    product_id: UUID
    quantity: int
    price_at_order: Decimal
    total_volume: Decimal
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")

        if self.price_at_order < 0:
            raise ValueError("Price cannot be negative")

        if self.total_volume < 0:
            raise ValueError("Total volume cannot be negative")

    @property
    def total_price(self) -> Decimal:
        return self.price_at_order * self.quantity


@dataclass(slots=True)
class Order:
    warehouse_id: UUID
    created_by_id: UUID
    retail_point_id: UUID
    id: UUID = field(default_factory=uuid4)
    visit_id: UUID | None = None
    status: OrderStatus = OrderStatus.PENDING
    total_amount: Decimal = field(default=Decimal("0.00"))
    total_volume: Decimal = field(default=Decimal("0.000"))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    items: list[OrderItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.total_amount < 0:
            raise ValueError("Total amount cannot be negative")

        if self.total_volume < 0:
            raise ValueError("Total volume cannot be negative")

    def add_item(self, item: OrderItem) -> None:
        if item.order_id != self.id:
            raise ValueError("Order item belongs to another order")

        self.items.append(item)
        self.total_amount += item.total_price
        self.total_volume += item.total_volume
        self._touch()

    def remove_item(self, product_id: UUID) -> None:
        item = next(
            (item for item in self.items if item.product_id == product_id),
            None,
        )

        if item is None:
            raise ValueError("Order item not found")

        self.items.remove(item)
        self.total_amount -= item.total_price
        self.total_volume -= item.total_volume
        self._touch()

    def clear_items(self) -> None:
        self.items.clear()
        self.total_amount = Decimal("0.00")
        self.total_volume = Decimal("0.000")
        self._touch()

    def confirm(self) -> None:
        if self.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be confirmed")

        if not self.items:
            raise ValueError("Order must contain at least one item")

        self.status = OrderStatus.CONFIRMED
        self._touch()

    def ship(self) -> None:
        if self.status != OrderStatus.CONFIRMED:
            raise ValueError("Only confirmed orders can be shipped")

        self.status = OrderStatus.SHIPPED
        self._touch()

    def cancel(self) -> None:
        if self.status == OrderStatus.SHIPPED:
            raise ValueError("Shipped order cannot be cancelled")

        if self.status == OrderStatus.CANCELLED:
            raise ValueError("Order is already cancelled")

        self.status = OrderStatus.CANCELLED
        self._touch()

    def recalculate(self) -> None:
        self.total_amount = sum(
            (item.total_price for item in self.items),
            Decimal("0.00"),
        )

        self.total_volume = sum(
            (item.total_volume for item in self.items),
            Decimal("0.000"),
        )

        self._touch()

    def _touch(self) -> None:
        self.updated_at = datetime.now(UTC)
