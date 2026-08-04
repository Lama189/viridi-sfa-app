import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import (
    StockTransactionType,
    TransactionActorType,
)

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.products import Product
    from app.infrastructure.postgres.models.warehouses import Warehouse


class StockTransaction(BaseModel):
    __tablename__ = "stock_transactions"

    __table_args__ = (
        Index(
            "idx_stock_tx_warehouse_product_created",
            "warehouse_id",
            "product_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    product_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
    )

    quantity_delta: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    transaction_type: Mapped[StockTransactionType] = mapped_column(
        SQLEnum(StockTransactionType, name="stock_transaction_type_enum"),
        nullable=False,
    )

    reference_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    reference_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    actor_type: Mapped[TransactionActorType] = mapped_column(
        SQLEnum(TransactionActorType, name="transaction_actor_type_enum"),
        nullable=False,
        default=TransactionActorType.SYSTEM,
    )

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    warehouse: Mapped[Warehouse] = relationship(
        back_populates="transactions",
    )

    product: Mapped[Product] = relationship(
        back_populates="transactions",
    )
