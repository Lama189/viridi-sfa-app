from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, UUID4

from app.domain.enums import OrderStatus


class OrderItemCreateRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    warehouse_id: UUID
    retail_point_id: UUID
    visit_id: UUID | None = None
    items: list[OrderItemCreateRequest]


class OrderItemResponse(BaseModel):
    id: UUID4
    order_id: UUID4
    product_id: UUID4
    quantity: int
    price_at_order: Decimal
    total_volume: Decimal

    model_config = {
        "from_attributes": True
    }


class OrderResponse(BaseModel):
    id: UUID4
    warehouse_id: UUID4
    created_by_id: UUID4
    retail_point_id: UUID4
    visit_id: UUID4 | None = None
    status: OrderStatus
    total_amount: Decimal
    total_volume: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {
        "from_attributes": True
    }