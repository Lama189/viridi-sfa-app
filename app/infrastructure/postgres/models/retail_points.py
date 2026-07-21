from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
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


class RetailPoint(BaseModel):
    __tablename__ = "retail_points"

    __table_args__ = (
        Index("idx_retail_points_mon", "visit_mon"),
        Index("idx_retail_points_tue", "visit_tue"),
        Index("idx_retail_points_wed", "visit_wed"),
        Index("idx_retail_points_thu", "visit_thu"),
        Index("idx_retail_points_fri", "visit_fri"),
        Index("idx_retail_points_sat", "visit_sat"),
        Index("idx_retail_points_sun", "visit_sun"),
    )

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

    photo_url: Mapped[str | None] = mapped_column(String(255))

    visit_mon: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_tue: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_wed: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_thu: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_fri: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_sat: Mapped[bool] = mapped_column(Boolean, default=False)
    visit_sun: Mapped[bool] = mapped_column(Boolean, default=False)

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