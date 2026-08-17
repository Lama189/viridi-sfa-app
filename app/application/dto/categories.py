from dataclasses import dataclass
from uuid import UUID


@dataclass(slots=True, frozen=True)
class CategoryCreateDTO:
    name: str


@dataclass(slots=True, frozen=True)
class CategoryUpdateDTO:
    name: str | None = None
    is_active: bool | None = None


@dataclass(slots=True, frozen=True)
class CategoryDTO:
    id: UUID
    name: str
    is_active: bool = True
