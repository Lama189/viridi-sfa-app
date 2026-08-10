from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.enums import (
    StockReferenceType,
    StockTransactionType,
    TransactionActorType,
)


class StockCreateRequest(BaseModel):
    warehouse_id: UUID
    product_id: UUID


class StockOperationRequest(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    actor_type: TransactionActorType = TransactionActorType.EMPLOYEE
    created_by_id: UUID | None = None
    reference_id: UUID | None = None
    reference_type: StockReferenceType = StockReferenceType.RECEIPT


class StockAdjustRequest(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    new_quantity: int
    reference_id: UUID | None = None


class StockResponse(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockTransactionResponse(BaseModel):
    id: UUID
    warehouse_id: UUID
    product_id: UUID
    quantity_delta: int
    transaction_type: StockTransactionType
    reference_type: StockReferenceType
    reference_id: UUID | None = None
    actor_type: TransactionActorType
    created_by_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
