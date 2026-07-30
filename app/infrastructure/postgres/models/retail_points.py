from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import ClientType

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.employees import Employee
    from app.infrastructure.postgres.models.invite_codes import RetailPointInviteCode
    from app.infrastructure.postgres.models.orders import Order
    from app.infrastructure.postgres.models.retail_point_members import RetailPointMember
    from app.infrastructure.postgres.models.visits import Visit
    from app.infrastructure.postgres.models.retail_point_assignments import RetailPointAssignment
    from app.infrastructure.postgres.models.visit_plan_items import VisitPlanItem
    from app.infrastructure.postgres.models.visit_schedule_rules import VisitScheduleRule


class RetailPoint(BaseModel):
    __tablename__ = "retail_points"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)

    legal_name: Mapped[str | None] = mapped_column(String(150))

    client_type: Mapped[ClientType] = mapped_column(
        Enum(ClientType, name="client_type"),
        default=ClientType.C,
        nullable=False,
    )

    address: Mapped[str] = mapped_column(Text, nullable=False)

    landmark: Mapped[str | None] = mapped_column(Text)

    contact_person: Mapped[str | None] = mapped_column(String(100))

    phone_number: Mapped[str | None] = mapped_column(String(20))

    inn: Mapped[str | None] = mapped_column(String(9))

    checking_account: Mapped[str | None] = mapped_column(String(20))

    bank_name: Mapped[str | None] = mapped_column(String(150))

    mfo: Mapped[str | None] = mapped_column(String(5))

    oked: Mapped[str | None] = mapped_column(String(5))

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6)
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6)
    )

    photo_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("media_objects.id", ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by_employee_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
    )

    created_by: Mapped["Employee | None"] = relationship(
        back_populates="retail_points",
        foreign_keys=[created_by_employee_id]
    )

    visits: Mapped[list["Visit"]] = relationship(
        back_populates="retail_point",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="retail_point",
    )

    members: Mapped[list["RetailPointMember"]] = relationship(
        back_populates="retail_point",
    )

    invite_codes: Mapped[list["RetailPointInviteCode"]] = relationship(
        back_populates="retail_point",
    )

    assignment: Mapped["RetailPointAssignment"] = relationship(
        back_populates="retail_point",
        uselist=False,
    )

    visit_plan_items: Mapped[list["VisitPlanItem"]] = relationship(
        back_populates="retail_point",
    )

    visit_schedule_rules: Mapped[list["VisitScheduleRule"]] = relationship(
        back_populates="retail_point",
    )