from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.application.dto.products import ProductShortDTO
from app.domain.enums import OrderStatus


@dataclass(slots=True, frozen=True)
class OrderItemCreateDTO:
    product_id: UUID
    quantity: int


@dataclass(slots=True, frozen=True)
class OrderCreateDTO:
    warehouse_id: UUID
    retail_point_id: UUID
    items: list[OrderItemCreateDTO]
    visit_id: UUID | None = None


@dataclass(slots=True, frozen=True)
class OrderItemDTO:
    id: UUID
    order_id: UUID
    product_id: UUID
    quantity: int
    price_at_order: Decimal
    total_volume: Decimal
    product: ProductShortDTO | None = None


@dataclass(slots=True, frozen=True)
class UserShortDTO:
    id: UUID
    full_name: str


@dataclass(slots=True, frozen=True)
class OrderShortDTO:
    id: UUID
    status: OrderStatus
    total_amount: Decimal
    total_volume: Decimal
    created_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class OrderDTO:
    id: UUID
    status: OrderStatus
    total_amount: Decimal
    total_volume: Decimal
    warehouse_id: UUID
    retail_point_id: UUID
    created_by_id: UUID
    retail_point_name: str | None = None
    retail_point_address: str | None = None
    warehouse_name: str | None = None
    created_by_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    visit_id: UUID | None = None
    items: list[OrderItemDTO] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class AcceptDeliveryDTO:
    order_id: UUID
    employee_id: UUID
    visit_id: UUID
