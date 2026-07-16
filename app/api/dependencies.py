from fastapi import Depends
from collections.abc import AsyncGenerator
from typing import Annotated

from app.core.config import get_settings

from app.infrastructure.postgres.uow import PostgresUnitOfWork

from app.application.interfaces.uow import IUnitOfWork
from app.application.services.warehouses import WarehousesService


settings = get_settings()


async def get_uow() -> AsyncGenerator[IUnitOfWork, None]:
    async with PostgresUnitOfWork() as uow:
        yield uow

async def get_warehouses_service(uow: Annotated[IUnitOfWork, Depends(get_uow)]) -> WarehousesService:
    return WarehousesService(uow)