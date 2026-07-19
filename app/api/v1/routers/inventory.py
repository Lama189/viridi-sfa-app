from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.inventory import (
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.application.services.warehouses import WarehousesService
from app.api.dependencies import get_warehouses_service


router = APIRouter(prefix="/api/v1/warehouses", tags=["Warehouses"])


@router.post(
    path="",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_warehouse(
    dto: WarehouseCreate,
    service: Annotated[WarehousesService, Depends(get_warehouses_service)]
):
    return await service.create_warehouse(dto)


@router.get(
    path="",
    response_model=list[WarehouseResponse],
    status_code=status.HTTP_200_OK,
)
async def get_warehouses(
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
    only_active: bool = True,
):
    return await service.get_all_warehouses(only_active=only_active)


@router.get(
    "/{warehouse_id}",
    response_model=WarehouseResponse,
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
    "/{warehouse_id}",
    response_model=WarehouseResponse,
)
async def update_warehouse(
    warehouse_id: UUID,
    dto: WarehouseUpdate,
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
):
    try:
        return await service.update_warehouse(warehouse_id, dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )