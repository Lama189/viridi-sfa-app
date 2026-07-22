from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.orders import Order
    from app.infrastructure.postgres.models.stocks import Stock
    from app.infrastructure.postgres.models.stock_transactions import StockTransaction


class Warehouse(BaseModel):
    __tablename__ = "warehouses"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    address: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    stocks: Mapped[list["Stock"]] = relationship(
        back_populates="warehouse",
        cascade="all, delete-orphan",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="warehouse",
    )

    transactions: Mapped[list["StockTransaction"]] = relationship(
        back_populates="warehouse"
    )
