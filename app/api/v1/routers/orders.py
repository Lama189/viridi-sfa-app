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
    DeliverOrderRequest,
    OrderResponse,
)
from app.application.dto.orders import (
    OrderCreateDTO,
    OrderItemCreateDTO,
)
from app.application.services.orders import OrdersService, parse_order_statuses
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
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        app_dto = OrderCreateDTO(
            warehouse_id=dto.warehouse_id,
            retail_point_id=dto.retail_point_id,
            source_visit_id=dto.source_visit_id,
            planned_visit_id=dto.planned_visit_id,
            actual_visit_id=dto.actual_visit_id,
            items=[
                OrderItemCreateDTO(
                    product_id=item.product_id,
                    quantity=item.quantity,
                )
                for item in dto.items
            ],
        )
        return await service.create_order(user, app_dto)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
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
    return await service.list_orders(
        statuses=parse_order_statuses(statuses),
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
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        return await service.get_order_for_user(order_id, user)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
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
        await service.cancel_for_client(order_id, client.id)
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
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
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
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
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
):
    try:
        return await service.complete_assembly(order_id, employee.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    path="/load-today",
    response_model=list[OrderResponse],
)
async def load_today_orders(
    service: Annotated[OrdersService, Depends(get_orders_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
):
    try:
        return await service.load_today_orders(employee.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    path="/{order_id}/load",
    response_model=OrderResponse,
)
async def load_order(
    order_id: UUID,
    service: Annotated[OrdersService, Depends(get_orders_service)],
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
):
    try:
        return await service.load_order(order_id, employee.id)
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
    path="/{order_id}/deliver",
    response_model=OrderResponse,
)
async def deliver_order(
    order_id: UUID,
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
    service: Annotated[OrdersService, Depends(get_orders_service)],
    body: DeliverOrderRequest | None = None,
):
    try:
        visit_id = body.visit_id if body else None
        return await service.deliver_for_user(
            order_id=order_id, user=user, visit_id=visit_id
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
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
