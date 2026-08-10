from dataclasses import dataclass
from uuid import UUID

from app.domain.enums import StockReferenceType, TransactionActorType


@dataclass(slots=True, frozen=True)
class StockCreateDTO:
    warehouse_id: UUID
    product_id: UUID


@dataclass(slots=True, frozen=True)
class StockOperationDTO:
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    actor_type: TransactionActorType
    reference_type: StockReferenceType
    reference_id: UUID | None = None
    created_by_id: UUID | None = None


@dataclass(slots=True, frozen=True)
class StockBatchItemDTO:
    product_id: UUID
    quantity: int


@dataclass(slots=True, frozen=True)
class StockBatchOperationDTO:
    warehouse_id: UUID
    items: list[StockBatchItemDTO]
    actor_type: TransactionActorType
    reference_type: StockReferenceType
    reference_id: UUID
    created_by_id: UUID | None = None
