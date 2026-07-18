from uuid import UUID

from pydantic import BaseModel, Field


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
