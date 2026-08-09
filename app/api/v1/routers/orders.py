from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    allow_all_staff,
    get_current_client,
    get_current_user,
    get_orders_service,
)
from app.api.v1.schemas.orders import (
    CreateOrderRequest,
    OrderResponse,
)
from app.application.services.orders import OrdersService
from app.core.exceptions import InvalidOrderStatusError
from app.domain.entities.auth import AuthenticatedClient, AuthenticatedEmployee
from app.domain.enums import OrderStatus

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
    path="",
    response_model=list[OrderResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_orders(
    service: Annotated[OrdersService, Depends(get_orders_service)],
    statuses: Annotated[
        list[str] | None,
        Query(description="Фильтр по статусам заказов"),
    ] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
):
    parsed_statuses: list[OrderStatus] | None = None

    if statuses:
        parsed_statuses = []
        for st in statuses:
            try:
                parsed_statuses.append(OrderStatus(st))
            except ValueError:
                raise InvalidOrderStatusError()

    return await service.list_orders(
        statuses=parsed_statuses,
        limit=limit,
        offset=offset,
    )


@router.get(
    path="/counters",
    response_model=dict[OrderStatus, int],
    dependencies=[Depends(allow_all_staff)],
)
async def get_orders_counters(
    service: Annotated[OrdersService, Depends(get_orders_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
):
    """Возвращает словарь с количеством заказов по каждому состоянию: {"pending": 3, "confirmed": 2, ...}"""
    return await service.get_counts_by_status(employee_id=employee.id)


@router.get(
    path="/{order_id}",
    response_model=OrderResponse,
)
async def get_order(
    order_id: UUID,
    user: Annotated[AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        order = await service.get_by_id(order_id)

        if isinstance(user, AuthenticatedClient) and order.created_by_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your order"
            )

        return order

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    path="/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_order(
    order_id: UUID,
    client: Annotated[AuthenticatedClient, Depends(get_current_client)],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        order = await service.get_by_id(order_id)
        if order.created_by_id != client.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your order",
            )
        await service.cancel(order_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    path="/{order_id}/confirm",
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
    path="/{order_id}/cancel",
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
    path="/{order_id}/ship",
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


@router.post(
    path="/{order_id}/start-assembly",
    response_model=OrderResponse,
)
async def start_order_assembly(
    order_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)]
):
    try:
        return await service.start_assembly(order_id, employee.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    path="/{order_id}/assemble",
    response_model=OrderResponse,
)
async def assemble_order(
    order_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)]
):
    try:
        return await service.complete_assembly(order_id, employee.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    path="/{order_id}/deliver",
    response_model=OrderResponse,
)
async def deliver_order(
    order_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)]
):
    try:
        return await service.deliver(order_id, employee.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
