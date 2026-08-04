from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class Client:
    phone: str
    full_name: str
    password_hash: str | None = None
    id: UUID = field(default_factory=uuid4)
    telegram_chat_id: int | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def telegram_id(self) -> int | None:
        return self.telegram_chat_id


