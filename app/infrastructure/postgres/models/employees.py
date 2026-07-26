from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Enum,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.postgres.models.base_model import BaseModel
from app.infrastructure.postgres.models.enums import EmployeeRole 

if TYPE_CHECKING:
    from app.infrastructure.postgres.models.retail_points import RetailPoint
    from app.infrastructure.postgres.models.visits import Visit
    from app.infrastructure.postgres.models.retail_point_assignments import RetailPointAssignment
    from app.infrastructure.postgres.models.visit_plans import VisitPlan


class Employee(BaseModel):
    __tablename__ = "employees"

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

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False, 
    )

    role: Mapped[EmployeeRole] = mapped_column(
        Enum(EmployeeRole, name="employee_role"),
        nullable=False,
        default=EmployeeRole.AGENT,
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
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
        back_populates="employee",
    )

    retail_point_assignments: Mapped[list["RetailPointAssignment"]] = relationship(
        back_populates="employee",
        foreign_keys="RetailPointAssignment.employee_id",
    )

    visit_plans: Mapped[list["VisitPlan"]] = relationship(
        back_populates="employee",
    )