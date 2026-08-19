from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RegisterDeviceRequest(BaseModel):
    fcm_token: str = Field(min_length=10, max_length=512)
    device_type: str = Field(default="android", max_length=50)


class RemoveDeviceRequest(BaseModel):
    fcm_token: str = Field(min_length=10, max_length=512)


class DeviceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    fcm_token: str
    device_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
