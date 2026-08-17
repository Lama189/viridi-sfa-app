from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class TokenResponseDTO:
    access_token: str
    refresh_token: str
    user_id: UUID


@dataclass(slots=True, frozen=True)
class RefreshTokenDTO:
    refresh_token: str
