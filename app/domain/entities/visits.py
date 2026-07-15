from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(slots=True)
class VisitPhoto:
    visit_id: UUID
    photo_url: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class Visit:
    agent_id: UUID
    retail_point_id: UUID
    id: UUID = field(default_factory=uuid4)
    check_in_time: datetime = field(default_factory=datetime.now)
    check_out_time: datetime | None = None
    actual_latitude: Decimal | None = None
    actual_longitude: Decimal | None = None
    status: str = "completed"
    comment: str | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass(slots=True)
class VisitWithPhotos:
    visit: Visit
    photos: list[VisitPhoto] = field(default_factory=list)
