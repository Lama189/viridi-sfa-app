from uuid import UUID

from pydantic import BaseModel, Field

from app.infrastructure.postgres.models.enums import EmployeeRole


class EmployeeCreate(BaseModel):
    phone: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Номер телефона сотрудника",
        json_schema_extra={"example": "+998901234567"},
    )
    password_hash: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Хэш пароля сотрудника",
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


class EmployeeCachedDTO(BaseModel):
    id: UUID
    phone: str
    full_name: str
    role: EmployeeRole
    is_active: bool

    model_config = {
        "from_attributes": True,
    }
