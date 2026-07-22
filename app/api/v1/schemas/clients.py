import re
from uuid import UUID
from pydantic import BaseModel, Field, field_validator



class ClientLoginDTO(BaseModel):
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Номер телефона клиента",
        json_schema_extra={"example": "+998901234567"},
    )
    telegram_chat_id: int | None = Field(
        default=None,
        description="Telegram chat ID клиента",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"\+998\d{9}", v):
            raise ValueError("Неверный формат номера. Ожидается +998XXXXXXXXX")
        return v
    

class ClientCreate(BaseModel):
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Номер телефона клиента",
        json_schema_extra={"example": "+998901234567"},
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Полное имя клиента",
        json_schema_extra={"example": "Иванов Иван"},
    )
    telegram_chat_id: int | None = Field(
        default=None,
        description="Telegram chat ID клиента",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"\+998\d{9}", v):
            raise ValueError("Неверный формат номера. Ожидается +998XXXXXXXXX")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Имя не может быть пустым")
        return v.strip()


class ClientUpdate(BaseModel):
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
    telegram_chat_id: int | None = Field(
        default=None,
        description="Новый Telegram chat ID",
    )
    is_active: bool | None = Field(
        None,
        description="Статус активности клиента",
    )


class ClientResponse(BaseModel):
    id: UUID
    phone: str
    full_name: str
    telegram_chat_id: int | None
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class ClientWithTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    client: ClientResponse

    model_config = {
        "from_attributes": True,
    }


class ClientCachedDTO(BaseModel):
    id: UUID
    phone: str                                     
    is_active: bool                 
    telegram_chat_id: int | None   

    model_config = {
        "from_attributes": True,
    }


class ClientConfirm(BaseModel):
    phone: str
    telegram_chat_id: int
    full_name: str | None


class ClientRegisterRequest(BaseModel):
    invite_code: str
    phone: str
    full_name: str
    telegram_chat_id: int