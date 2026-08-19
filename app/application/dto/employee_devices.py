from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True, frozen=True)
class RegisterDeviceDTO:
    employee_id: UUID
    fcm_token: str
    device_type: str = "android"


@dataclass(slots=True, frozen=True)
class EmployeeDeviceDTO:
    id: UUID
    employee_id: UUID
    fcm_token: str
    device_type: str
    updated_at: datetime
