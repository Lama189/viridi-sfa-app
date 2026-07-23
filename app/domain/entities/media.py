from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass(slots=True)
class MediaFile:
    bucket: str
    object_name: str
    content_type: str
    size: int
    uploaded_by: UUID

    id: UUID = field(default_factory=uuid4)

    original_filename: str | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )