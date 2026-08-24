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
from app.application.services.orders import OrdersService
from app.core.exceptions import InvalidOrderStatusError
from app.domain.entities.auth import AuthenticatedClient, AuthenticatedEmployee
from app.domain.enums import OrderStatus

from app.domain.entities.clients import Client
from app.domain.entities.retail_point_members import RetailPointMember

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
        warehouse_id = dto.warehouse_id
        retail_point_id = dto.retail_point_id

        if isinstance(user, AuthenticatedClient):
            if retail_point_id is None and user.telegram_chat_id:
                member = await service._uow.retail_point_members.get_by_telegram_id(
                    user.telegram_chat_id
                )
                if member:
                    retail_point_id = member.retail_point_id

            if retail_point_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Retail point ID is required",
                )

            is_member = await service._uow.retail_point_members.exists(
                retail_point_id, user.id
            )
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your retail point",
                )
            client_id = user.id
        else:
            if retail_point_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Retail point ID is required",
                )

            members = await service._uow.retail_point_members.get_by_retail_point(
                retail_point_id
            )
            if members:
                client_id = members[0].client_id
            else:
                rp = await service._uow.retail_points.get_by_id(retail_point_id)
                if rp is None:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Retail point {retail_point_id} not found",
                    )
                client = None
                if rp.phone_number:
                    client = await service._uow.clients.get_by_phone(rp.phone_number)
                if client is None:
                    phone = rp.phone_number or f"+99899{str(retail_point_id.int)[:7]}"
                    client = Client(
                        phone=phone,
                        full_name=rp.contact_person or rp.name,
                        is_active=True,
                    )
                    await service._uow.clients.add(client)
                await service._uow.retail_point_members.add(
                    RetailPointMember(
                        retail_point_id=retail_point_id,
                        client_id=client.id,
                    )
                )
                client_id = client.id

        if warehouse_id is None:
            active_warehouses = await service._uow.warehouses.list(is_active=True)
            if active_warehouses:
                warehouse_id = active_warehouses[0].id

        if warehouse_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active warehouse found for the order",
            )

        app_dto = OrderCreateDTO(
            warehouse_id=warehouse_id,
            retail_point_id=retail_point_id,
            planned_visit_id=dto.planned_visit_id,
            items=[
                OrderItemCreateDTO(
                    product_id=item.product_id,
                    quantity=item.quantity,
                )
                for item in dto.items
            ],
        )
        return await service.create(client_id, app_dto)
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
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
    service: Annotated[OrdersService, Depends(get_orders_service)],
):
    try:
        order = await service.get_by_id(order_id)

        if isinstance(user, AuthenticatedClient) and order.created_by_id != user.id:
            is_member = await service._uow.retail_point_members.exists(
                order.retail_point_id, user.id
            )
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Not your order"
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
            is_member = await service._uow.retail_point_members.exists(
                order.retail_point_id, client.id
            )
            if not is_member:
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
        order = await service.get_by_id(order_id)
        if isinstance(user, AuthenticatedClient) and order.created_by_id != user.id:
            is_member = await service._uow.retail_point_members.exists(
                order.retail_point_id, user.id
            )
            if not is_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your order",
                )
        employee_id = user.id if isinstance(user, AuthenticatedEmployee) else None
        visit_id = body.visit_id if body else None
        return await service.deliver(
            order_id, employee_id=employee_id, visit_id=visit_id
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
