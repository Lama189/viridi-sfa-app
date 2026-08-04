from decimal import Decimal

from pydantic import UUID4, BaseModel, Field


class WarehouseCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Название склада",
        json_schema_extra={"example": "Склад Сергели"},
    )
    address: str | None = Field(
        None,
        description="Физический адрес склада",
        json_schema_extra={
            "example": "г. Ташкент, Сергелийский район, ул. Янги Сергели"
        },
    )


class WarehouseUpdate(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=100, description="Новое название склада"
    )
    address: str | None = Field(None, description="Новый адрес склада")
    is_active: bool | None = None


class WarehouseResponse(BaseModel):
    id: UUID4
    name: str
    address: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    price: Decimal = Field(
        ..., gt=0, description="Цена товара в сумах (UZS)", examples=[53000.00]
    )
    category_id: UUID4 = Field(..., description="ID существующей категории")
    volume: Decimal = Field(default=Decimal("0.000"), description="Объем в м³")
    weight: Decimal = Field(default=Decimal("0.000"), description="Вес в кг")
    items_in_box: int = Field(default=1, gt=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    price: Decimal | None = Field(None, gt=0, description="Цена товара в сумах (UZS)")
    category_id: UUID4 | None = Field(None, description="ID существующей категории")
    volume: Decimal | None = Field(None, description="Объем в м³")
    weight: Decimal | None = Field(None, description="Вес в кг")
    items_in_box: int | None = Field(None, gt=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: UUID4
    name: str
    price: Decimal
    category_id: UUID4
    volume: Decimal
    weight: Decimal
    items_in_box: int
    photo_url: str | None = Field(None, description="Относительный путь к фото в MinIO")

    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = Field(
        None,
        description="Статус активности категории",
    )


class CategoryResponse(BaseModel):
    id: UUID4
    name: str
    is_active: bool

    model_config = {"from_attributes": True}


class ProductWithCategoryResponse(ProductResponse):
    category: CategoryResponse

    model_config = {"from_attributes": True}
