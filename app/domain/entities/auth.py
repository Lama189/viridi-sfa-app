from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.clients import Client
from app.domain.entities.employees import Employee
from app.infrastructure.postgres.models.enums import EmployeeRole


@dataclass(slots=True, frozen=True)
class AuthenticatedEmployee:
    id: UUID
    phone: str
    full_name: str
    role: EmployeeRole
    is_active: bool

    @classmethod
    def from_entity(cls, employee: Employee) -> "AuthenticatedEmployee":
        return cls(
            id=employee.id,
            phone=employee.phone,
            full_name=employee.full_name,
            role=employee.role,
            is_active=employee.is_active,
        )


@dataclass(slots=True, frozen=True)
class AuthenticatedClient:
    id: UUID
    phone: str
    full_name: str
    is_active: bool
    telegram_chat_id: int | None = None

    @classmethod
    def from_entity(cls, client: Client) -> "AuthenticatedClient":
        return cls(
            id=client.id,
            phone=client.phone,
            full_name=client.full_name,
            is_active=client.is_active,
            telegram_chat_id=client.telegram_chat_id,
        )
