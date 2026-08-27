from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import allow_admin, get_products_service
from app.api.v1.schemas.inventory import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from app.application.dto.products import ProductCreateDTO, ProductUpdateDTO
from app.application.services.products import ProductsService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.post(
    path="",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allow_admin)],
)
async def create_product(
    dto: ProductCreate,
    service: Annotated[ProductsService, Depends(get_products_service)],
):
    try:
        app_dto = ProductCreateDTO(
            name=dto.name,
            price=dto.price,
            category_id=dto.category_id,
            photo_id=dto.photo_id,
            volume=dto.volume,
            weight=dto.weight,
            items_in_box=dto.items_in_box,
        )
        return await service.create_product(app_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get(
    path="",
    response_model=list[ProductResponse],
)
async def get_products(
    service: Annotated[ProductsService, Depends(get_products_service)],
    only_active: bool = True,
):
    return await service.get_all_products(only_active=only_active)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
)
async def get_product(
    product_id: UUID,
    service: Annotated[ProductsService, Depends(get_products_service)],
):
    product = await service.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {product_id} not found",
        )
    return product


@router.patch(
    "/{product_id}", response_model=ProductResponse, dependencies=[Depends(allow_admin)]
)
async def update_product(
    product_id: UUID,
    dto: ProductUpdate,
    service: Annotated[ProductsService, Depends(get_products_service)],
):
    try:
        app_dto = ProductUpdateDTO(
            name=dto.name,
            price=dto.price,
            category_id=dto.category_id,
            photo_id=dto.photo_id,
            volume=dto.volume,
            weight=dto.weight,
            items_in_box=dto.items_in_box,
            is_active=dto.is_active,
        )
        return await service.update_product(product_id, app_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_admin)],
)
async def delete_product(
    product_id: UUID,
    service: Annotated[ProductsService, Depends(get_products_service)],
):
    try:
        await service.delete_product(product_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
