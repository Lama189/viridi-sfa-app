from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    id: UUID
    employee_id: UUID
    title: str
    body: str
    notification_type: str
    payload: dict = Field(default_factory=dict)
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    unread_count: int
