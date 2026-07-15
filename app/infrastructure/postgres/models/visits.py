from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import VisitStatus

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.users import User
    from app.infrastructure.postgres.models.orders import Order
    from app.infrastructure.postgres.models.retail_points import RetailPoint
    from app.infrastructure.postgres.models.visit_photos import VisitPhoto


class Visit(BaseModel):
    __tablename__ = "visits"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )

    retail_point_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("retail_points.id", ondelete="RESTRICT"),
        nullable=False,
    )

    actual_latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6)
    )

    actual_longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6)
    )

    status: Mapped[VisitStatus] = mapped_column(
        Enum(VisitStatus, name="visit_status"),
        default=VisitStatus.COMPLETED,
        nullable=False,
    )

    comment: Mapped[str | None] = mapped_column(Text)

    agent: Mapped["User"] = relationship(
        back_populates="visits",
    )

    retail_point: Mapped["RetailPoint"] = relationship(
        back_populates="visits",
    )

    photos: Mapped[list["VisitPhoto"]] = relationship(
        back_populates="visit",
        cascade="all, delete-orphan",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="visit",
    )
