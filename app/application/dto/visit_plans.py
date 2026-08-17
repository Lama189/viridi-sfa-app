from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from app.application.dto.retail_points import RetailPointShortDTO
from app.domain.enums import VisitPlanItemStatus, VisitPlanStatus, Weekday


@dataclass(slots=True, frozen=True)
class GenerateVisitPlanDTO:
    employee_id: UUID
    plan_date: date
    overwrite: bool = True


@dataclass(slots=True, frozen=True)
class VisitPlanItemDTO:
    order: int
    status: VisitPlanItemStatus
    retail_point_id: UUID
    retail_point: RetailPointShortDTO | None = None


@dataclass(slots=True, frozen=True)
class VisitPlanDTO:
    id: UUID
    employee_id: UUID
    date: date
    weekday: Weekday
    status: VisitPlanStatus
    items: list[VisitPlanItemDTO] = field(default_factory=list)
