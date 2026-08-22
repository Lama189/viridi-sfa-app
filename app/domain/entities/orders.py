from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.enums import OrderStatus


@dataclass(slots=True)
class RetailPointShort:
    id: UUID
    name: str
    address: str


@dataclass(slots=True)
class WarehouseShort:
    id: UUID
    name: str


@dataclass(slots=True)
class UserShort:
    id: UUID
    full_name: str


@dataclass(slots=True)
class ProductShort:
    id: UUID
    name: str
    code: str | None = None
    unit_of_measure: str | None = None


@dataclass(slots=True)
class OrderItem:
    order_id: UUID
    product_id: UUID
    quantity: int
    price_at_order: Decimal
    total_volume: Decimal
    id: UUID = field(default_factory=uuid4)
    product_name: str | None = None
    product: ProductShort | None = None

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
    planned_visit_id: UUID | None = None
    planned_delivery_date: date | None = None
    delivery_agent_name: str | None = None
    actual_visit_id: UUID | None = None
    status: OrderStatus = OrderStatus.PENDING

    total_amount: Decimal = field(default=Decimal("0.00"))
    total_volume: Decimal = field(default=Decimal("0.000"))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    items: list[OrderItem] = field(default_factory=list)
    retail_point: RetailPointShort | None = None
    warehouse: WarehouseShort | None = None
    created_by: UserShort | None = None

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

    def confirm(self, planned_visit_id: UUID | None = None) -> None:
        if self.status != OrderStatus.PENDING:
            raise ValueError("Only pending orders can be confirmed")

        if not self.items:
            raise ValueError("Order must contain at least one item")

        self.status = OrderStatus.CONFIRMED
        if planned_visit_id is not None:
            self.planned_visit_id = planned_visit_id
        self._touch()

    def plan_delivery(self, planned_visit_id: UUID) -> None:
        if self.status in (
            OrderStatus.LOADED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ):
            raise ValueError(
                f"Cannot plan delivery for order in status '{self.status}'"
            )

        self.planned_visit_id = planned_visit_id
        self._touch()

    def start_assembly(self) -> None:
        if self.status not in (OrderStatus.PENDING, OrderStatus.CONFIRMED):
            raise ValueError(
                f"Cannot start assembly for order in status '{self.status}'"
            )

        if not self.items:
            raise ValueError("Order must contain at least one item")

        self.status = OrderStatus.ASSEMBLY_STARTED
        self._touch()

    def complete_assembly(self) -> None:
        if self.status != OrderStatus.ASSEMBLY_STARTED:
            raise ValueError(
                f"Cannot complete assembly for order in status '{self.status}'"
            )

        self.status = OrderStatus.ASSEMBLED
        self._touch()

    def load(self) -> None:
        if self.status != OrderStatus.ASSEMBLED:
            raise ValueError(f"Cannot load order in status '{self.status}'")

        self.status = OrderStatus.LOADED
        self._touch()

    def ship(self) -> None:
        if self.status not in (
            OrderStatus.CONFIRMED,
            OrderStatus.ASSEMBLY_STARTED,
            OrderStatus.ASSEMBLED,
            OrderStatus.LOADED,
        ):
            raise ValueError(f"Cannot ship order in status '{self.status}'")

        self.status = OrderStatus.SHIPPED
        self._touch()

    def deliver(self, actual_visit_id: UUID | None = None) -> None:
        if self.status not in (
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.ASSEMBLY_STARTED,
            OrderStatus.ASSEMBLED,
            OrderStatus.LOADED,
            OrderStatus.SHIPPED,
        ):
            raise ValueError(f"Cannot deliver order in status '{self.status}'")

        if actual_visit_id is not None:
            self.actual_visit_id = actual_visit_id
        self.status = OrderStatus.DELIVERED
        self._touch()

    def cancel(self) -> None:
        if self.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise ValueError(f"Order in status '{self.status}' cannot be cancelled")

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
