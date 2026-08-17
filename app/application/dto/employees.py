from dataclasses import dataclass
from uuid import UUID

from app.domain.enums import EmployeeRole


@dataclass(slots=True, frozen=True)
class EmployeeCreateDTO:
    phone: str
    password: str
    full_name: str
    role: EmployeeRole = EmployeeRole.AGENT


@dataclass(slots=True, frozen=True)
class EmployeeUpdateDTO:
    phone: str | None = None
    password_hash: str | None = None
    full_name: str | None = None
    role: EmployeeRole | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class EmployeeLoginDTO:
    phone: str
    password: str


@dataclass(slots=True, frozen=True)
class EmployeeDTO:
    id: UUID
    phone: str
    full_name: str
    role: EmployeeRole
    is_active: bool = True


@dataclass(slots=True, frozen=True)
class EmployeeWithTokensDTO:
    access_token: str
    refresh_token: str
    employee: EmployeeDTO
