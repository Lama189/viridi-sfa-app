from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.retail_points import (
    CreateRetailPointRequest,
    UpdateRetailPointRequest,
    RetailPointResponse
)
from app.application.services.retail_points import RetailPointsService
from app.api.dependencies import get_retail_points_service, allow_admin, allow_all_staff, allow_retail_points_view
from app.domain.entities.employees import Employee


router = APIRouter(prefix="/api/v1/retail_points", tags=["RetailPoints"])


@router.post(
    path="",
    response_model=RetailPointResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_retail_point(
    dto: CreateRetailPointRequest,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
    employee: Annotated[Employee, Depends(allow_all_staff)]
):
    try:
        retail_point = await service.create_retail_point(dto, employee.id) 

        if dto.owner_client_full_name and dto.owner_client_phone:
            await service.connect_client_to_point(
                retail_point.id, 
                dto.owner_client_phone, 
                dto.owner_client_full_name
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    
@router.get(
    path="/by_owner/{owner_id}",
    response_model=list[RetailPointResponse],
    dependencies=[Depends(allow_retail_points_view)]
)
async def get_retail_points_by_owner_id(
    owner_id: UUID,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)]
):
    return await service.get_by_owner(owner_id)


@router.get(
    "/{retail_point_id}",
    response_model=RetailPointResponse
)
async def get_retail_point(
    retail_point_id: UUID,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)]
):
    retail_point = await service.get_by_id(retail_point_id)
    if not retail_point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Retail point {retail_point_id} not found",
        )
    return retail_point


@router.patch(
    "/{retail_point_id}",
    response_model=RetailPointResponse,
    dependencies=[Depends(allow_all_staff)]
)
async def update_retail_point(
    retail_point_id: UUID,
    dto: UpdateRetailPointRequest,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    try:
        return await service.update_retail_point(retail_point_id, dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{retail_point_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def delete_retail_point(
    retail_point_id: UUID,
    service: Annotated[RetailPointsService, Depends(get_retail_points_service)],
):
    try:
        await service.delete_retail_point(retail_point_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
