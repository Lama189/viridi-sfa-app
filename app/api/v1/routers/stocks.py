from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import allow_all_staff, get_stocks_service
from app.api.v1.schemas.inventory import ProductWithStockResponse
from app.api.v1.schemas.stocks import (
    StockAdjustRequest,
    StockResponse,
    StockTransactionResponse,
)
from app.application.interfaces.services.stocks import IStockService
from app.domain.entities.auth import AuthenticatedEmployee

router = APIRouter(prefix="/api/v1/stocks", tags=["Stocks"])


@router.get(
    "/transactions",
    response_model=list[StockTransactionResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_stock_transactions(
    service: Annotated[IStockService, Depends(get_stocks_service)],
    warehouse_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    reference_id: UUID | None = Query(default=None),
):
    return await service.list_transactions(
        warehouse_id=warehouse_id,
        product_id=product_id,
        reference_id=reference_id,
    )


@router.post(
    "/adjust",
    response_model=StockResponse,
    status_code=status.HTTP_200_OK,
)
async def adjust_stock(
    dto: StockAdjustRequest,
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
    service: Annotated[IStockService, Depends(get_stocks_service)],
):
    try:
        return await service.adjust_stock(
            warehouse_id=dto.warehouse_id,
            product_id=dto.product_id,
            new_quantity=dto.new_quantity,
            actor_id=employee.id,
            reference_id=dto.reference_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=list[ProductWithStockResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_warehouse_stocks(
    warehouse_id: Annotated[UUID, Query(description="ID выбираемого склада")],
    service: Annotated[IStockService, Depends(get_stocks_service)],
):
    return await service.get_warehouse_inventory(warehouse_id=warehouse_id)
