from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.employees import Employee
    from app.infrastructure.postgres.models.retail_points import RetailPoint


class RetailPointAssignment(BaseModel):
    __tablename__ = "retail_point_assignments"

    __table_args__ = (
        Index(
            "idx_retail_point_assignment_employee",
            "employee_id",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    retail_point_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("retail_points.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    employee_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    retail_point: Mapped[RetailPoint] = relationship(
        back_populates="assignment",
    )

    employee: Mapped[Employee] = relationship(
        back_populates="retail_point_assignments",
    )
