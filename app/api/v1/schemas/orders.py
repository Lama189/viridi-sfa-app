from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.v1.schemas.common import (
    RetailPointShortResponse,
    UserShortResponse,
    WarehouseShortResponse,
)
from app.domain.enums import OrderStatus


class ProductShortResponse(BaseModel):
    id: UUID
    name: str
    code: str | None = None
    unit_of_measure: str | None = None

    model_config = {"from_attributes": True}


class OrderItemCreateRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    warehouse_id: UUID | None = None
    retail_point_id: UUID | None = None
    visit_id: UUID | None = None
    items: list[OrderItemCreateRequest]


class OrderItemResponse(BaseModel):
    id: UUID
    order_id: UUID
    product: ProductShortResponse 
    quantity: int
    price_at_order: Decimal
    total_volume: Decimal

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: UUID
    status: OrderStatus
    total_amount: Decimal
    total_volume: Decimal
    retail_point: RetailPointShortResponse
    warehouse: WarehouseShortResponse
    created_by: UserShortResponse
    created_at: datetime | None = None 
    updated_at: datetime | None = None
    visit_id: UUID | None = None

    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}
