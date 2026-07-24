from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import VisitStatus

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.employees import Employee
    from app.infrastructure.postgres.models.retail_points import RetailPoint
    from app.infrastructure.postgres.models.visit_media import VisitMedia
    from app.infrastructure.postgres.models.visit_debts import VisitDebt


class Visit(BaseModel):
    __tablename__ = "visits"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False,
    )

    retail_point_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("retail_points.id", ondelete="RESTRICT"),
        nullable=False,
    )

    status: Mapped[VisitStatus] = mapped_column(
        Enum(VisitStatus, name="visit_status"),
        default=VisitStatus.IN_PROGRESS,
        nullable=False,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    employee: Mapped["Employee"] = relationship(
        back_populates="visits",
    )

    retail_point: Mapped["RetailPoint"] = relationship(
        back_populates="visits",
    )

    media: Mapped[list["VisitMedia"]] = relationship(
        back_populates="visit",
        cascade="all, delete-orphan",
    )

    debts: Mapped[list["VisitDebt"]] = relationship(
        back_populates="visit",
        cascade="all, delete-orphan",
    )