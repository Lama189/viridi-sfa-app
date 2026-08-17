from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.application.dto.categories import CategoryDTO


@dataclass(slots=True, frozen=True)
class ProductCreateDTO:
    name: str
    price: Decimal
    category_id: UUID
    volume: Decimal = Decimal("0.000")
    weight: Decimal = Decimal("0.000")
    items_in_box: int = 1


@dataclass(slots=True, frozen=True)
class ProductUpdateDTO:
    name: str | None = None
    price: Decimal | None = None
    category_id: UUID | None = None
    volume: Decimal | None = None
    weight: Decimal | None = None
    items_in_box: int | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class ProductDTO:
    id: UUID
    name: str
    price: Decimal
    category_id: UUID
    volume: Decimal = Decimal("0.000")
    weight: Decimal = Decimal("0.000")
    items_in_box: int = 1
    photo_url: str | None = None
    is_active: bool = True


@dataclass(slots=True, frozen=True)
class ProductShortDTO:
    id: UUID
    name: str
    code: str | None = None
    unit_of_measure: str | None = None


@dataclass(slots=True, frozen=True)
class ProductWithCategoryDTO:
    product: ProductDTO
    category: CategoryDTO
