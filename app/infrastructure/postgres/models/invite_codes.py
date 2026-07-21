from typing import TYPE_CHECKING
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    ForeignKey,
    String,
    Boolean,
    DateTime,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel


if TYPE_CHECKING:
    from app.infrastructure.postgres.models.retail_points import RetailPoint
    from app.infrastructure.postgres.models.employees import Employee
    from app.infrastructure.postgres.models.clients import Client


class RetailPointInviteCode(BaseModel):
    __tablename__ = "retail_point_invite_codes"


    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    retail_point_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "retail_points.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    code_hash: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_activated_client_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "clients.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    last_activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by_employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            "employees.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


    retail_point: Mapped["RetailPoint"] = relationship(
        back_populates="invite_codes",
    )

    last_activated_client: Mapped["Client | None"] = relationship(
        foreign_keys=[last_activated_client_id],
    )

    created_by: Mapped["Employee"] = relationship()