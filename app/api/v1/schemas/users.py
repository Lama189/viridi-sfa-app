from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.enums import UserRole


class UserCreate(BaseModel):
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Номер телефона пользователя",
        json_schema_extra={"example": "+998901234567"},
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Полное имя пользователя",
        json_schema_extra={"example": "Иванов Иван"},
    )
    role: UserRole = Field(
        default=UserRole.CLIENT,
        description="Роль пользователя",
    )
    telegram_chat_id: int | None = Field(
        default=None,
        description="Telegram chat ID пользователя",
    )


class UserUpdate(BaseModel):
    phone: str | None = Field(
        None,
        min_length=1,
        max_length=20,
        description="Новый номер телефона",
    )
    full_name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Новое полное имя",
    )
    role: UserRole | None = Field(
        None,
        description="Новая роль пользователя",
    )
    telegram_chat_id: int | None = Field(
        default=None,
        description="Новый Telegram chat ID",
    )
    is_active: bool | None = Field(
        None,
        description="Статус активности пользователя",
    )


class UserResponse(BaseModel):
    id: UUID
    phone: str
    full_name: str
    role: UserRole
    telegram_chat_id: int | None
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class UserCachedDTO(BaseModel):
    id: UUID
    phone: str                     
    role: UserRole                  
    is_active: bool                 
    telegram_chat_id: int | None   

    model_config = {
        "from_attributes": True,
    }


class LoginDTO(BaseModel):
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Номер телефона пользователя",
        json_schema_extra={"example": "+998901234567"},
    )
