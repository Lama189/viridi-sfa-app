from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4


@dataclass(slots=True)
class ClientInviteCode:
    retail_point_id: UUID
    code_hash: str
    created_by_employee_id: UUID

    id: UUID = field(default_factory=uuid4)

    is_active: bool = True

    last_activated_client_id: UUID | None = None
    last_activated_at: datetime | None = None

    expires_at: datetime | None = None

    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def create(
        cls,
        *,
        retail_point_id: UUID,
        code_hash: str,
        created_by_employee_id: UUID,
        expires_in: timedelta | None = None,
        now: datetime | None = None,
    ) -> "ClientInviteCode":
        current_time = now or datetime.now(timezone.utc)
        return cls(
            retail_point_id=retail_point_id,
            code_hash=code_hash,
            created_by_employee_id=created_by_employee_id,
            expires_at=(
                current_time + expires_in
                if expires_in
                else None
            ),
            created_at=current_time,
            updated_at=current_time,
        )

    def activate(self, client_id: UUID, *, now: datetime | None = None) -> None:
        current_time = now or datetime.now(timezone.utc)

        if not self.is_available(now=current_time):
            raise ValueError("Invite code is not available")

        self.last_activated_client_id = client_id
        self.last_activated_at = current_time
        self.is_active = True

        self._touch(now=current_time)

    def regenerate(self, new_hash: str, *, now: datetime | None = None) -> None:
        current_time = now or datetime.now(timezone.utc)
        self.code_hash = new_hash
        self.is_active = True
        self.last_activated_client_id = None
        self.last_activated_at = None

        self._touch(now=current_time)

    def deactivate(self, *, now: datetime | None = None) -> None:
        self.is_active = False
        self._touch(now=now)

    def change_expiration(
        self, expires_at: datetime | None, *, now: datetime | None = None
    ) -> None:
        self.expires_at = expires_at
        self._touch(now=now)

    def is_available(self, *, now: datetime | None = None) -> bool:
        if not self.is_active:
            return False

        current_time = now or datetime.now(timezone.utc)

        if self.expires_at is not None:
            return current_time < self.expires_at

        return True

    def _touch(self, *, now: datetime | None = None) -> None:
        self.updated_at = now or datetime.now(timezone.utc)