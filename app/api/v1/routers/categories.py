from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas.inventory import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)
from app.application.services.categories import CategoriesService
from app.api.dependencies import get_categories_service, allow_admin


router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.post(
    path="",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allow_admin)]
)
async def create_category(
    dto: CategoryCreate,
    service: Annotated[CategoriesService, Depends(get_categories_service)],
):
    try:
        return await service.create_category(dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    path="",
    response_model=list[CategoryResponse],
)
async def get_categories(
    service: Annotated[CategoriesService, Depends(get_categories_service)],
    only_active: bool = True,
):
    return await service.get_all_categories(only_active=only_active)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
)
async def get_category(
    category_id: UUID,
    service: Annotated[CategoriesService, Depends(get_categories_service)],
):
    category = await service.get_by_id(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found",
        )
    return category


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(allow_admin)]
)
async def update_category(
    category_id: UUID,
    dto: CategoryUpdate,
    service: Annotated[CategoriesService, Depends(get_categories_service)],
):
    try:
        return await service.update_category(category_id, dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)]
)
async def delete_category(
    category_id: UUID,
    service: Annotated[CategoriesService, Depends(get_categories_service)],
):
    try:
        await service.delete_category(category_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
