from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class NotificationCreateDTO:
    employee_id: UUID
    title: str
    body: str
    notification_type: str = "general"
    payload: dict = field(default_factory=dict)


@dataclass(slots=True)
class NotificationDTO:
    id: UUID
    employee_id: UUID
    title: str
    body: str
    notification_type: str
    payload: dict
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None
