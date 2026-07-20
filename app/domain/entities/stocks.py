from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.enums import StockTransactionType, TransactionActorType


@dataclass(slots=True)
class Stock:
    warehouse_id: UUID
    product_id: UUID
    quantity: int = 0
    reserved_quantity: int = 0


@dataclass(slots=True)
class StockTransaction:
    warehouse_id: UUID
    product_id: UUID
    quantity_delta: int
    transaction_type: StockTransactionType
    reference_type: str
    reference_id: UUID
    id: UUID = field(default_factory=uuid4)
    actor_type: TransactionActorType = TransactionActorType.SYSTEM
    created_by_id: UUID | None = None
    created_at: datetime = field(default_factory=datetime.now)
