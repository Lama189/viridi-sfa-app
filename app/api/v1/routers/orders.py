from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    allow_all_staff,
    get_current_client,
    get_orders_service,
)
from app.api.v1.schemas.orders import (
    CreateOrderRequest,
    OrderResponse,
)
from app.application.services.orders import OrdersService
from app.domain.entities.auth import AuthenticatedClient

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


@router.post(
    path="",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    dto: CreateOrderRequest,
    client: Annotated[AuthenticatedClient, Depends(get_current_client)],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        return await service.create(client.id, dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: UUID,
    client: Annotated[AuthenticatedClient, Depends(get_current_client)],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    order = await service._uow.orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order {order_id} not found",
        )
    if order.created_by_id != client.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your order",
        )
    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_order(
    order_id: UUID,
    client: Annotated[AuthenticatedClient, Depends(get_current_client)],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        order = await service._uow.orders.get_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Order {order_id} not found",
            )
        if order.created_by_id != client.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your order",
            )
        await service.cancel(order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{order_id}/confirm",
    response_model=OrderResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def confirm_order(
    order_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        return await service.confirm(order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def cancel_order_by_staff(
    order_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        return await service.cancel(order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/{order_id}/ship",
    response_model=OrderResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def ship_order(
    order_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        return await service.ship(order_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
