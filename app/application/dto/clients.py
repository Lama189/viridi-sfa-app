from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class ClientCreateDTO:
    phone: str
    full_name: str
    telegram_chat_id: int | None = None


@dataclass(slots=True, frozen=True)
class ClientUpdateDTO:
    phone: str | None = None
    full_name: str | None = None
    telegram_chat_id: int | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class ClientRegisterDTO:
    invite_code: str
    phone: str
    full_name: str
    telegram_chat_id: int | None = None


@dataclass(slots=True, frozen=True)
class ClientLoginDTO:
    phone: str
    telegram_chat_id: int | None = None


@dataclass(slots=True, frozen=True)
class ClientTelegramLoginDTO:
    init_data: str


@dataclass(slots=True, frozen=True)
class ClientDTO:
    id: UUID
    phone: str
    full_name: str
    telegram_chat_id: int | None = None
    is_active: bool = True


@dataclass(slots=True, frozen=True)
class ClientWithTokensDTO:
    access_token: str
    refresh_token: str
    client: ClientDTO
