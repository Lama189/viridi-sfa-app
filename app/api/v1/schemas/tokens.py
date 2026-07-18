from uuid import UUID
from pydantic import BaseModel


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    user_id: UUID

    class Config:
        from_attributes = True


class RefreshTokenDTO(BaseModel):
    refresh_token: str