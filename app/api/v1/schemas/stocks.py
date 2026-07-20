from uuid import UUID
from pydantic import BaseModel

from app.domain.enums import StockReferenceType, TransactionActorType


class StockCreateRequest(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    

class StockOperationRequest(BaseModel):
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    actor_type: TransactionActorType
    created_by_id: UUID | None
    reference_id: UUID 
    reference_type: StockReferenceType