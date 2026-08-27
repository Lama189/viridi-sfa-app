from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass(slots=True)
class Warehouse:
    name: str
    id: UUID = field(default_factory=uuid4)
    address: str | None = None
    is_active: bool = True


@dataclass(slots=True)
class Category:
    name: str
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True


@dataclass(slots=True)
class Product:
    category_id: UUID
    name: str
    price: Decimal
    id: UUID = field(default_factory=uuid4)
    photo_id: UUID | None = None
    volume: Decimal = field(default=Decimal("0.000"))
    weight: Decimal = field(default=Decimal("0.000"))
    items_in_box: int = 1
    is_active: bool = True


@dataclass(slots=True)
class Stock:
    warehouse_id: UUID
    product_id: UUID
    quantity: int = 0
