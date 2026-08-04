from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import VisitPlanStatus

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.employees import Employee
    from app.infrastructure.postgres.models.visit_plan_items import VisitPlanItem


class VisitPlan(BaseModel):
    __tablename__ = "visit_plans"

    __table_args__ = (
        UniqueConstraint(
            "employee_id", "plan_date", name="uq_visit_plan_employee_date"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )

    plan_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[VisitPlanStatus] = mapped_column(
        Enum(VisitPlanStatus, name="visit_plan_status"),
        default=VisitPlanStatus.PLANNED,
        nullable=False,
    )

    employee: Mapped[Employee] = relationship(
        back_populates="visit_plans",
    )

    items: Mapped[list[VisitPlanItem]] = relationship(
        back_populates="visit_plan",
        cascade="all, delete-orphan",
    )
