from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.application.dto.orders import OrderShortDTO
from app.application.dto.retail_points import RetailPointShortDTO
from app.domain.enums import VisitStatus


@dataclass(slots=True, frozen=True)
class StartVisitDTO:
    retail_point_id: UUID


@dataclass(slots=True, frozen=True)
class AddVisitDebtDTO:
    amount: Decimal
    comment: str | None = None


@dataclass(slots=True, frozen=True)
class UpdateVisitDebtDTO:
    amount: Decimal
    comment: str | None = None


@dataclass(slots=True, frozen=True)
class VisitDTO:
    id: UUID
    employee_id: UUID
    retail_point_id: UUID
    status: VisitStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class VisitDebtDTO:
    id: UUID
    visit_id: UUID
    amount: Decimal
    comment: str | None = None
    created_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class VisitMediaDTO:
    id: UUID
    visit_id: UUID
    media_id: UUID
    created_at: datetime | None = None


@dataclass(slots=True, frozen=True)
class VisitDetailsDTO:
    id: UUID
    status: VisitStatus
    retail_point: RetailPointShortDTO
    started_at: datetime | None = None
    finished_at: datetime | None = None
    orders: list[OrderShortDTO] = field(default_factory=list)
    debts: list[VisitDebtDTO] = field(default_factory=list)
    media: list[VisitMediaDTO] = field(default_factory=list)
