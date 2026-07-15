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

    # Requisites (Uzbekistan)
    inn: str | None = None
    checking_account: str | None = None
    bank_name: str | None = None
    mfo: str | None = None
    oked: str | None = None

    # Geo
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    photo_url: str | None = None

    # Visit schedule
    visit_mon: bool = False
    visit_tue: bool = False
    visit_wed: bool = False
    visit_thu: bool = False
    visit_fri: bool = False
    visit_sat: bool = False
    visit_sun: bool = False

    created_by_user_id: UUID | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
