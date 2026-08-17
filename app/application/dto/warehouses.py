from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class WarehouseCreateDTO:
    name: str
    address: str | None = None


@dataclass(slots=True, frozen=True)
class WarehouseUpdateDTO:
    name: str | None = None
    address: str | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class WarehouseDTO:
    id: UUID
    name: str
    address: str | None = None
    is_active: bool = True


@dataclass(slots=True, frozen=True)
class WarehouseShortDTO:
    id: UUID
    name: str
