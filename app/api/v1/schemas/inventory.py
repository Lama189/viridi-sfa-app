from pydantic import BaseModel, Field, UUID4


class WarehouseCreate(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100, 
        description="Название склада", 
        json_schema_extra={"example": "Склад Сергели"}
    )
    address: str | None = Field(
        None, 
        description="Физический адрес склада", 
        json_schema_extra={"example": "г. Ташкент, Сергелийский район, ул. Янги Сергели"}
    )


class WarehouseUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100, description="Новое название склада")
    address: str | None = Field(None, description="Новый адрес склада")
    is_active: bool | None = None


class WarehouseResponse(BaseModel):
    id: UUID4
    name: str
    address: str | None
    is_active: bool

    model_config = {
        "from_attributes": True  
    }