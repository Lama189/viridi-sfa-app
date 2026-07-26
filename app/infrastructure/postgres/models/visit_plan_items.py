from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import VisitPlanItemStatus

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.visit_plans import VisitPlan
    from app.infrastructure.postgres.models.retail_points import RetailPoint


class VisitPlanItem(BaseModel):
    __tablename__ = "visit_plan_items"

    __table_args__ = (
        CheckConstraint(
            "\"order\" >= 0",
            name="ck_visit_plan_item_order_non_negative",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    visit_plan_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("visit_plans.id", ondelete="CASCADE"),
        nullable=False,
    )

    retail_point_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("retail_points.id", ondelete="RESTRICT"),
        nullable=False,
    )

    order: Mapped[int] = mapped_column(
        "order",
        Integer,
        nullable=False,
    )

    status: Mapped[VisitPlanItemStatus] = mapped_column(
        Enum(VisitPlanItemStatus, name="visit_plan_item_status"),
        default=VisitPlanItemStatus.PENDING,
        nullable=False,
    )

    visit_plan: Mapped["VisitPlan"] = relationship(
        back_populates="items",
    )

    retail_point: Mapped["RetailPoint"] = relationship(
        back_populates="visit_plan_items",
    )
