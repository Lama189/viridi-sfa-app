from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field

from app.domain.enums import ClientType


class CreateRetailPointRequest(BaseModel):
    name: str = Field(max_length=150)
    legal_name: str | None = Field(default=None, max_length=150)

    client_type: ClientType = ClientType.C

    address: str
    landmark: str | None = None

    contact_person: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=20)

    inn: str | None = Field(default=None, max_length=9)
    checking_account: str | None = Field(default=None, max_length=20)
    bank_name: str | None = Field(default=None, max_length=150)
    mfo: str | None = Field(default=None, max_length=5)
    oked: str | None = Field(default=None, max_length=5)

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    photo_url: str | None = None

    visit_mon: bool = False
    visit_tue: bool = False
    visit_wed: bool = False
    visit_thu: bool = False
    visit_fri: bool = False
    visit_sat: bool = False
    visit_sun: bool = False


class UpdateRetailPointRequest(BaseModel):
    name: str | None = None
    legal_name: str | None = None

    client_type: ClientType | None = None

    address: str | None = None
    landmark: str | None = None

    contact_person: str | None = None
    phone_number: str | None = None

    inn: str | None = None
    checking_account: str | None = None
    bank_name: str | None = None
    mfo: str | None = None
    oked: str | None = None

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    photo_url: str | None = None

    visit_mon: bool | None = None
    visit_tue: bool | None = None
    visit_wed: bool | None = None
    visit_thu: bool | None = None
    visit_fri: bool | None = None
    visit_sat: bool | None = None
    visit_sun: bool | None = None

    is_active: bool | None = None


class RetailPointResponse(BaseModel):
    id: UUID

    name: str
    legal_name: str | None

    client_type: ClientType

    address: str
    landmark: str | None

    contact_person: str | None
    phone_number: str | None

    inn: str | None
    checking_account: str | None
    bank_name: str | None
    mfo: str | None
    oked: str | None

    latitude: Decimal | None
    longitude: Decimal | None

    photo_url: str | None

    visit_mon: bool
    visit_tue: bool
    visit_wed: bool
    visit_thu: bool
    visit_fri: bool
    visit_sat: bool
    visit_sun: bool

    is_active: bool

    invite_code: str

    model_config = {
        "from_attributes": True
    }