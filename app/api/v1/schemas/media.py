from uuid import UUID
from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    id: UUID
    original_object_name: str
    thumbnail_object_name: str
    content_type: str
    size: int

    model_config = {
        "from_attributes": True  
    }