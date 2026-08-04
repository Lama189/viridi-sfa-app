from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import UUID4, BaseModel

from app.domain.enums import VisitStatus


class StartVisitRequest(BaseModel):
    retail_point_id: UUID


class AttachMediaRequest(BaseModel):
    media_id: UUID


class AddDebtRequest(BaseModel):
    amount: Decimal
    comment: str | None = None


class UpdateDebtRequest(BaseModel):
    amount: Decimal
    comment: str | None = None


class VisitResponse(BaseModel):
    id: UUID4
    employee_id: UUID4
    retail_point_id: UUID4
    status: VisitStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class VisitMediaResponse(BaseModel):
    id: UUID4
    visit_id: UUID4
    media_id: UUID4
    created_at: datetime

    model_config = {"from_attributes": True}


class VisitDebtResponse(BaseModel):
    id: UUID4
    visit_id: UUID4
    amount: Decimal
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
