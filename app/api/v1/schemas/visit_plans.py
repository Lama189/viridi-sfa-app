from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import UUID4, BaseModel

from app.domain.enums import VisitPlanItemStatus, VisitPlanStatus, Weekday


class GenerateVisitPlanRequest(BaseModel):
    employee_id: UUID
    plan_date: date


class VisitPlanItemRetailPointResponse(BaseModel):
    name: str
    address: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    model_config = {"from_attributes": True}


class VisitPlanItemResponse(BaseModel):
    order: int
    status: VisitPlanItemStatus
    retail_point_id: UUID4
    retail_point: VisitPlanItemRetailPointResponse

    model_config = {"from_attributes": True}


class VisitPlanResponse(BaseModel):
    id: UUID4
    employee_id: UUID4
    date: date
    weekday: Weekday
    status: VisitPlanStatus
    items: list[VisitPlanItemResponse] = []

    model_config = {"from_attributes": True}
