from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.v1.schemas.visits import OrderShortResponse, VisitDebtResponse
from app.domain.enums import ClientType


class VisitsDatesDTO(BaseModel):
    mon: bool = False
    tue: bool = False
    wed: bool = False
    thu: bool = False
    fri: bool = False
    sat: bool = False
    sun: bool = False


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

    photo_id: UUID | None = None

    visits: VisitsDatesDTO = Field(default_factory=VisitsDatesDTO)


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

    photo_id: UUID | None = None

    visits: VisitsDatesDTO = Field(default_factory=VisitsDatesDTO)

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

    photo_id: UUID | None

    visits: VisitsDatesDTO = Field(default_factory=VisitsDatesDTO)

    is_active: bool

    model_config = {"from_attributes": True}


class RetailPointDetailsResponse(BaseModel):
    retail_point: RetailPointResponse
    orders: list[OrderShortResponse] = Field(default_factory=list)
    debts: list[VisitDebtResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class InviteCodeResponse(BaseModel):
    invite_code: str

    model_config = {"from_attributes": True}


class RetailPointWithCodeResponse(BaseModel):
    retail_point: RetailPointResponse
    invite_code: str

    model_config = {"from_attributes": True}


class BulkCreateRetailPointsResponse(BaseModel):
    created_count: int
    created: list[RetailPointResponse]

    model_config = {"from_attributes": True}


class RetailPointMemberResponse(BaseModel):
    id: UUID
    retail_point_id: UUID
    client_id: UUID

    model_config = {"from_attributes": True}


class AssignAgentRequest(BaseModel):
    employee_id: UUID


class RetailPointAssignmentResponse(BaseModel):
    id: UUID
    retail_point_id: UUID
    employee_id: UUID | None

    model_config = {"from_attributes": True}
