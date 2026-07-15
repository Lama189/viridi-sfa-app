from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Boolean,
    BigInteger,
    DateTime,
    Enum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import UserRole

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.retail_points import RetailPoint
    from app.infrastructure.postgres.models.visits import Visit
    from app.infrastructure.postgres.models.orders import Order


class User(BaseModel):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.CLIENT,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    telegram_chat_id: Mapped[int | None] = mapped_column(
        BigInteger,
        unique=True,
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    retail_points: Mapped[list["RetailPoint"]] = relationship(
        back_populates="created_by",
    )

    visits: Mapped[list["Visit"]] = relationship(
        back_populates="agent",
    )

    orders: Mapped[list["Order"]] = relationship(
        back_populates="created_by",
    )
