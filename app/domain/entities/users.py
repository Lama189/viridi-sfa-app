from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.enums import UserRole


@dataclass(slots=True)
class User:
    phone: str  
    full_name: str
    id: UUID = field(default_factory=uuid4)
    role: UserRole = UserRole.CLIENT
    telegram_chat_id: int | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
