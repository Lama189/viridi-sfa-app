from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.v1.schemas.common import CategoryResponse, WarehouseShortResponse


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
    id: UUID
    name: str
    address: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    price: Decimal = Field(
        ..., gt=0, description="Цена товара в сумах (UZS)", examples=[53000.00]
    )
    category_id: UUID = Field(..., description="ID существующей категории")
    photo_id: UUID | None = Field(
        None, description="ID загруженного медиа-объекта фото товара"
    )
    volume: Decimal = Field(default=Decimal("0.000"), description="Объем в м³")
    weight: Decimal = Field(default=Decimal("0.000"), description="Вес в кг")
    items_in_box: int = Field(default=1, gt=0)


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    price: Decimal | None = Field(None, gt=0, description="Цена товара в сумах (UZS)")
    category_id: UUID | None = Field(None, description="ID существующей категории")
    photo_id: UUID | None = Field(
        None, description="ID загруженного медиа-объекта фото товара"
    )
    volume: Decimal | None = Field(None, description="Объем в м³")
    weight: Decimal | None = Field(None, description="Вес в кг")
    items_in_box: int | None = Field(None, gt=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    price: Decimal
    category_id: UUID
    photo_id: UUID | None = Field(
        None, description="ID загруженного медиа-объекта фото товара"
    )
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


class ProductWithCategoryResponse(ProductResponse):
    category: CategoryResponse

    model_config = {"from_attributes": True}


class StockSummaryResponse(BaseModel):
    warehouse: WarehouseShortResponse
    quantity: int = Field(description="Физический остаток")
    reserved_quantity: int = Field(description="Зарезервировано в заказах")
    available_quantity: int = Field(
        description="Доступно к продаже (quantity - reserved)"
    )
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProductWithStockResponse(BaseModel):
    id: UUID
    name: str
    price: Decimal
    volume: Decimal
    weight: Decimal
    items_in_box: int
    photo_id: UUID | None = None
    photo_url: str | None = None
    category: CategoryResponse
    stock: StockSummaryResponse | None = None

    model_config = {"from_attributes": True}
