from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import allow_all_staff, get_warehouses_service
from app.api.v1.schemas.inventory import (
    WarehouseCreate,
    WarehouseResponse,
    WarehouseUpdate,
)
from app.application.services.warehouses import WarehousesService

router = APIRouter(prefix="/api/v1/warehouses", tags=["Warehouses"])


@router.post(
    path="",
    response_model=WarehouseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_warehouse(
    dto: WarehouseCreate,
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
):
    return await service.create_warehouse(dto)


@router.get(
    path="",
    response_model=list[WarehouseResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(allow_all_staff)]
)
async def list_warehouses(
    service: Annotated[WarehousesService, Depends(get_warehouses_service)],
    is_active: bool = Query(default=True)
):
    return await service.list(is_active=is_active)


@router.get(
    path="/{warehouse_id}",
    response_model=WarehouseResponse,
    dependencies=[Depends(allow_all_staff)]
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
