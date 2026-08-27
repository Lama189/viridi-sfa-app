from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    allow_admin,
    allow_all_staff,
    get_warehouses_service,
)
from app.api.v1.schemas.inventory import (
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.application.dto.warehouses import WarehouseCreateDTO, WarehouseUpdateDTO
from app.application.services.warehouses import WarehousesService

router = APIRouter(prefix="/api/v1/warehouses", tags=["Warehouses"])


@router.post(
    path="",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allow_admin)],
)
async def create_warehouse(
    dto: WarehouseCreate,
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
):
    app_dto = WarehouseCreateDTO(name=dto.name, address=dto.address)
    return await service.create_warehouse(app_dto)


@router.get(
    path="",
    response_model=list[WarehouseResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(allow_all_staff)],
)
async def list_warehouses(
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
    is_active: bool = Query(default=True),
):
    return await service.list(is_active=is_active)


@router.get(
    path="/{warehouse_id}",
    response_model=WarehouseResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def get_warehouse(
    warehouse_id: UUID,
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
):
    warehouse = await service.get_by_id(warehouse_id)
    if not warehouse:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Warehouse {warehouse_id} not found",
        )
    return warehouse


@router.patch(
    path="/{warehouse_id}",
    response_model=WarehouseResponse,
    dependencies=[Depends(allow_admin)],
)
async def update_warehouse(
    warehouse_id: UUID,
    dto: WarehouseUpdate,
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
):
    try:
        app_dto = WarehouseUpdateDTO(
            name=dto.name, address=dto.address, is_active=dto.is_active
        )
        return await service.update_warehouse(warehouse_id, app_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
