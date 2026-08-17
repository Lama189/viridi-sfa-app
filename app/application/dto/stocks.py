from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.application.dto.categories import CategoryDTO
from app.domain.enums import (
    StockReferenceType,
    StockTransactionType,
    TransactionActorType,
)


@dataclass(slots=True, frozen=True)
class StockCreateDTO:
    warehouse_id: UUID
    product_id: UUID


@dataclass(slots=True, frozen=True)
class StockOperationDTO:
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    actor_type: TransactionActorType = TransactionActorType.EMPLOYEE
    reference_type: StockReferenceType = StockReferenceType.RECEIPT
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


@dataclass(slots=True, frozen=True)
class StockAdjustDTO:
    warehouse_id: UUID
    product_id: UUID
    new_quantity: int
    reference_id: UUID | None = None


@dataclass(slots=True, frozen=True)
class StockDTO:
    warehouse_id: UUID
    product_id: UUID
    quantity: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class StockSummaryDTO:
    warehouse_id: UUID
    warehouse_name: str
    quantity: int
    reserved_quantity: int
    available_quantity: int
    updated_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class StockTransactionDTO:
    id: UUID
    warehouse_id: UUID
    product_id: UUID
    quantity_delta: int
    transaction_type: StockTransactionType
    reference_type: StockReferenceType
    actor_type: TransactionActorType
    reference_id: UUID | None = None
    created_by_id: UUID | None = None
    created_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class ProductWithStockDTO:
    id: UUID
    name: str
    price: Decimal
    volume: Decimal
    weight: Decimal
    items_in_box: int
    category: CategoryDTO
    photo_url: str | None = None
    stock: StockSummaryDTO | None = None
