from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.enums import Weekday


@dataclass(slots=True)
class VisitScheduleRule:
    retail_point_id: UUID
    weekday: Weekday

    id: UUID = field(default_factory=uuid4)
    is_active: bool = True

    def activate(self) -> None:
        self.is_active = True

    def deactivate(self) -> None:
        self.is_active = False
