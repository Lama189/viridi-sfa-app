from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.enums import MediaBucket


@dataclass(slots=True, frozen=True)
class MediaUploadDTO:
    uploaded_by: UUID
    bucket: MediaBucket
    data: bytes
    content_type: str
    filename: str | None = None
    prefix: str | None = None


@dataclass(slots=True, frozen=True)
class MediaFileDTO:
    id: UUID
    original_object_name: str
    thumbnail_object_name: str
    content_type: str
    size: int
    bucket: str
    original_filename: str | None = None
    uploaded_by: UUID | None = None
    created_at: datetime | None = None
