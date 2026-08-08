import re
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.domain.enums import EmployeeRole


class EmployeeCreate(BaseModel):
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Номер телефона сотрудника",
        json_schema_extra={"example": "+998901234567"},
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Пароль сотрудника",
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Полное имя сотрудника",
        json_schema_extra={"example": "Иванов Иван"},
    )
    role: EmployeeRole = Field(
        default=EmployeeRole.AGENT,
        description="Роль сотрудника",
    )


class EmployeeUpdate(BaseModel):
    phone: str | None = Field(
        None,
        min_length=1,
        max_length=20,
        description="Новый номер телефона",
    )
    password_hash: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Новый хэш пароля",
    )
    full_name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Новое полное имя",
    )
    role: EmployeeRole | None = Field(
        None,
        description="Новая роль сотрудника",
    )
    is_active: bool | None = Field(
        None,
        description="Статус активности сотрудника",
    )


class EmployeeResponse(BaseModel):
    id: UUID
    phone: str
    full_name: str
    role: EmployeeRole
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class EmployeeLoginDTO(BaseModel):
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Номер телефона сотрудника",
        json_schema_extra={"example": "+998901234567"},
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=100,
        description="Сырой пароль сотрудника для проверки",
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.fullmatch(r"\+998\d{9}", v):
            raise ValueError("Неверный формат номера. Ожидается +998XXXXXXXXX")
        return v


class EmployeeWithTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    employee: EmployeeResponse

    model_config = {
        "from_attributes": True,
    }
