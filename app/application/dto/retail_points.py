from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

from app.domain.entities.visit_debts import VisitDebt
from app.domain.enums import ClientType


@dataclass(slots=True, frozen=True)
class VisitsDatesDTO:
    mon: bool = False
    tue: bool = False
    wed: bool = False
    thu: bool = False
    fri: bool = False
    sat: bool = False
    sun: bool = False


@dataclass(slots=True, frozen=True)
class RetailPointCreateDTO:
    name: str
    address: str
    legal_name: str | None = None
    client_type: ClientType = ClientType.C
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
    visits: VisitsDatesDTO = field(default_factory=VisitsDatesDTO)


@dataclass(slots=True, frozen=True)
class RetailPointUpdateDTO:
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
    visits: VisitsDatesDTO | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class RetailPointDTO:
    id: UUID
    name: str
    client_type: ClientType
    address: str
    is_active: bool = True
    total_debt: Decimal = Decimal("0.00")
    legal_name: str | None = None
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
    visits: VisitsDatesDTO = field(default_factory=VisitsDatesDTO)


@dataclass(slots=True, frozen=True)
class RetailPointShortDTO:
    id: UUID
    name: str
    address: str
    contact_person: str | None = None
    phone_number: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None


@dataclass(slots=True, frozen=True)
class RetailPointDebtorDTO:
    retail_point: RetailPointShortDTO
    total_debt: Decimal
    debts_count: int
    debts: list[VisitDebt] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class RetailPointMemberDTO:
    id: UUID
    retail_point_id: UUID
    client_id: UUID


@dataclass(slots=True, frozen=True)
class AssignAgentDTO:
    employee_id: UUID


@dataclass(slots=True, frozen=True)
class RetailPointAssignmentDTO:
    id: UUID
    retail_point_id: UUID
    employee_id: UUID | None = None


@dataclass(slots=True, frozen=True)
class RetailPointWithCodeDTO:
    retail_point: RetailPointDTO
    invite_code: str


@dataclass(slots=True, frozen=True)
class BulkCreateRetailPointsResultDTO:
    created_count: int
    created: list[RetailPointDTO]
