from dataclasses import dataclass, field
from datetime import datetime, UTC
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
    photo_id: UUID | None = None

    created_by_employee_id: UUID | None = None

    is_active: bool = True

    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self._validate_name()
        self._validate_address()
        self._validate_coordinates()
        self._validate_phone_number()

    def _validate_name(self) -> None:
        if not self.name.strip():
            raise ValueError("Retail point name cannot be empty.")

        if len(self.name) > 150:
            raise ValueError("Retail point name is too long.")

    def _validate_address(self) -> None:
        if not self.address.strip():
            raise ValueError("Retail point address cannot be empty.")

    def _validate_coordinates(self) -> None:
        if self.latitude is not None:
            if self.latitude < Decimal("-90") or self.latitude > Decimal("90"):
                raise ValueError("Latitude must be between -90 and 90.")

        if self.longitude is not None:
            if self.longitude < Decimal("-180") or self.longitude > Decimal("180"):
                raise ValueError("Longitude must be between -180 and 180.")

    def _validate_phone_number(self) -> None:
        if self.phone_number is None:
            return

        if len(self.phone_number) > 20:
            raise ValueError("Phone number is too long.")


@dataclass(frozen=True, slots=True)
class RetailPointIdentity:
    name: str
    address: str

    def __post_init__(self):
        object.__setattr__(
            self,
            "name",
            self.name.lower().strip()
        )
        object.__setattr__(
            self,
            "address",
            self.address.lower().strip()
        )

@dataclass(slots=True)
class BulkCreateRetailPointsResult:
    created: list[RetailPoint]
    
    @property
    def created_count(self) -> int:
        return len(self.created)