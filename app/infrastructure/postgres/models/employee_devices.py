from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.employees import Employee


class EmployeeDevice(BaseModel):
    __tablename__ = "employee_devices"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    employee_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    fcm_token: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        unique=True,
        index=True,
    )

    device_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="android",
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

    employee: Mapped[Employee] = relationship(
        "Employee",
        back_populates="devices",
    )
