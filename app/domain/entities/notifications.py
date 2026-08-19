from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class Notification:
    employee_id: UUID
    title: str
    body: str
    notification_type: str = "general"
    payload: dict = field(default_factory=dict)
    is_read: bool = False
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    read_at: datetime | None = None

    def mark_as_read(self) -> None:
        self.is_read = True
        self.read_at = datetime.now(UTC)
