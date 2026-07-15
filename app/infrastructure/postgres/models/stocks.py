from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.products import Product
    from app.infrastructure.postgres.models.warehouses import Warehouse


class Stock(BaseModel):
    __tablename__ = "stocks"

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_stock_quantity_positive"),
    )

    warehouse_id: Mapped[PG_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product_id: Mapped[PG_UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    warehouse: Mapped["Warehouse"] = relationship(
        back_populates="stocks",
    )

    product: Mapped["Product"] = relationship(
        back_populates="stocks",
    )
