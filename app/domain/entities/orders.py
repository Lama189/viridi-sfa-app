from dataclasses import dataclass, field
from datetime import datetime
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
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
