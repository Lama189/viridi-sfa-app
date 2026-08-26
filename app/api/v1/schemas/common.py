from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class WarehouseShortResponse(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class RetailPointShortResponse(BaseModel):
    id: UUID
    name: str
    address: str
    contact_person: str | None = None
    phone_number: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None

    model_config = {"from_attributes": True}


class UserShortResponse(BaseModel):
    id: UUID
    full_name: str

    model_config = {"from_attributes": True}


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    is_active: bool

    model_config = {"from_attributes": True}
