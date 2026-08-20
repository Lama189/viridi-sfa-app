from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Enum,
    ForeignKey,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.enums import OrderStatus
from app.infrastructure.postgres.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.clients import Client
    from app.infrastructure.postgres.models.order_items import OrderItem
    from app.infrastructure.postgres.models.retail_points import RetailPoint
    from app.infrastructure.postgres.models.visit_plans import VisitPlan
    from app.infrastructure.postgres.models.visits import Visit
    from app.infrastructure.postgres.models.warehouses import Warehouse


class Order(BaseModel):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    warehouse_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("warehouses.id", ondelete="RESTRICT"),
        nullable=False,
    )

    created_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="RESTRICT"),
        nullable=False,
    )

    retail_point_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("retail_points.id", ondelete="RESTRICT"),
        nullable=False,
    )

    planned_visit_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("visit_plans.id", ondelete="SET NULL"),
        nullable=True,
    )

    actual_visit_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("visits.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    total_volume: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
        default=Decimal("0.000"),
    )

    warehouse: Mapped[Warehouse] = relationship(
        back_populates="orders",
    )

    created_by: Mapped[Client] = relationship(
        back_populates="orders",
    )

    retail_point: Mapped[RetailPoint] = relationship(
        back_populates="orders",
    )

    planned_visit: Mapped[VisitPlan | None] = relationship(
        back_populates="orders",
        foreign_keys=[planned_visit_id],
    )

    actual_visit: Mapped[Visit | None] = relationship(
        back_populates="orders",
        foreign_keys=[actual_visit_id],
    )

    items: Mapped[list[OrderItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
