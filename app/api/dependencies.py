from fastapi import Depends
from collections.abc import AsyncGenerator
from typing import Annotated

from app.core.config import get_settings

from app.application.interfaces.uow import IUnitOfWork
from app.infrastructure.postgres.uow import PostgresUnitOfWork

from app.application.services.categories import CategoriesService
from app.application.services.warehouses import WarehousesService
from app.application.services.products import ProductsService
from app.application.services.retail_points import RetailPointsService


settings = get_settings()


async def get_uow() -> AsyncGenerator[IUnitOfWork, None]:
    async with PostgresUnitOfWork() as uow:
        yield uow

async def get_categories_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> CategoriesService:
    return CategoriesService(uow)

async def get_warehouses_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> WarehousesService:
    return WarehousesService(uow)

async def get_retail_points_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> RetailPointsService:
    return RetailPointsService(uow)

async def get_products_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> ProductsService:
    return ProductsService(uow)