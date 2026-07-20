from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemCreateRequest(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)


class CreateOrderRequest(BaseModel):
    warehouse_id: UUID
    retail_point_id: UUID
    visit_id: UUID | None = None
    items: list[OrderItemCreateRequest]