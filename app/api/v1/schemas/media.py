from uuid import UUID
from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    id: UUID
    bucket: str
    object_name: str
    url: str | None = None
    content_type: str
    size: int

    model_config = {
        "from_attributes": True  
    }