from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.enums import ClientType


@dataclass(slots=True)
class RetailPoint:
    name: str
    address: str
    
    id: UUID = field(default_factory=uuid4)
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
    photo_url: str | None = None

    visit_mon: bool = field(default=False)
    visit_tue: bool = field(default=False)
    visit_wed: bool = field(default=False)
    visit_thu: bool = field(default=False)
    visit_fri: bool = field(default=False)
    visit_sat: bool = field(default=False)
    visit_sun: bool = field(default=False)

    created_by_employee_id: UUID | None = None
    owner_client_id: UUID | None = None
    
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)