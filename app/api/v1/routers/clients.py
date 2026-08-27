from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    allow_all_staff,
    get_clients_auth_service,
    get_clients_service,
    get_current_user,
    get_orders_service,
    get_retail_point_members_service,
)
from app.api.v1.schemas.clients import (
    ClientJoinByInviteRequest,
    ClientRegisterRequest,
    ClientResponse,
    ClientTelegramLoginRequest,
    ClientUpdate,
    ClientWithTokensResponse,
)
from app.api.v1.schemas.orders import OrderResponse
from app.api.v1.schemas.tokens import RefreshTokenDTO, TokenResponseDTO
from app.application.dto.clients import (
    ClientRegisterDTO,
    ClientTelegramLoginDTO,
    ClientUpdateDTO,
)
from app.application.services.clients import (
    ClientsAuthService,
    ClientsService,
)
from app.application.services.members import RetailPointMembersService
from app.application.services.orders import OrdersService, parse_order_statuses
from app.core.config import get_settings
from app.core.exceptions import DomainError, UserNotActiveError, UserNotFoundError
from app.domain.entities.auth import AuthenticatedClient, AuthenticatedEmployee
from app.infrastructure.telegram import send_telegram_notification

router = APIRouter(prefix="/api/v1/clients", tags=["Clients"])


@router.post(
    "/register",
    response_model=ClientWithTokensResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    dto: ClientRegisterRequest,
    service: Annotated[ClientsAuthService, Depends(get_clients_auth_service)],
):
    app_dto = ClientRegisterDTO(
        invite_code=dto.invite_code,
        phone=dto.phone,
        full_name=dto.full_name,
        telegram_chat_id=dto.telegram_chat_id,
    )
    return await service.register(app_dto)


@router.post(
    "/telegram-login",
    response_model=ClientWithTokensResponse,
    status_code=status.HTTP_200_OK,
)
async def telegram_login(
    dto: ClientTelegramLoginRequest,
    service: Annotated[ClientsAuthService, Depends(get_clients_auth_service)],
):
    try:
        app_dto = ClientTelegramLoginDTO(init_data=dto.init_data)
        return await service.telegram_login(app_dto)
    except (ValueError, UserNotFoundError, UserNotActiveError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e) if str(e) else e.__class__.__name__,
        )


@router.post(
    "/join-by-invite",
    response_model=ClientWithTokensResponse,
    status_code=status.HTTP_200_OK,
)
async def join_by_invite(
    dto: ClientJoinByInviteRequest,
    service: Annotated[ClientsAuthService, Depends(get_clients_auth_service)],
):
    try:
        return await service.join_by_invite(
            invite_code=dto.invite_code,
            telegram_chat_id=dto.telegram_chat_id,
            client_id=dto.client_id,
        )
    except (ValueError, DomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/by-telegram/{telegram_chat_id}",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
)
async def get_by_telegram_chat_id(
    telegram_chat_id: int,
    service: Annotated[ClientsService, Depends(get_clients_service)],
):
    result = await service.get_by_telegram_chat_id_with_membership(telegram_chat_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    
    client, retail_point_id = result
    return ClientResponse(
        id=client.id,
        phone=client.phone,
        full_name=client.full_name,
        telegram_chat_id=client.telegram_chat_id,
        is_active=client.is_active,
        has_retail_point=retail_point_id is not None,
        retail_point_id=retail_point_id,
    )


@router.post(
    "/{client_id}/leave-retail-point",
    status_code=status.HTTP_200_OK,
)
async def leave_retail_point(
    client_id: UUID,
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
    service: Annotated[
        RetailPointMembersService, Depends(get_retail_point_members_service)
    ],
    clients_service: Annotated[ClientsService, Depends(get_clients_service)],
):
    if isinstance(user, AuthenticatedClient) and user.id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )

    try:
        client = await clients_service.get_client(client_id)
        await service.leave_by_client(client_id)

        if client and client.telegram_chat_id:
            settings = get_settings()
            await send_telegram_notification(
                chat_id=client.telegram_chat_id,
                text=(
                    "🚪 Вы успешно вышли из торговой точки.\n\n"
                    "Чтобы подключиться к новой торговой точке, нажмите /start и отправьте новый код приглашения."
                ),
                token=settings.telegram_bot_token,
            )
    except (UserNotFoundError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e) or "Client not found",
        )

    return {"status": "success", "message": "Successfully left retail point"}


@router.post(
    "/refresh",
    response_model=TokenResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def refresh(
    dto: RefreshTokenDTO,
    service: Annotated[ClientsAuthService, Depends(get_clients_auth_service)],
):
    try:
        return await service.refresh(dto.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
)
async def get_client(
    client_id: UUID,
    service: Annotated[
        ClientsService,
        Depends(get_clients_service),
    ],
):
    client = await service.get_client(client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    return client


@router.get(
    "/{client_id}/orders",
    response_model=list[OrderResponse],
)
async def list_client_orders(
    client_id: UUID,
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
    service: Annotated[OrdersService, Depends(get_orders_service)],
    clients_service: Annotated[ClientsService, Depends(get_clients_service)],
    statuses: Annotated[list[str] | None, Query()] = None,
):
    if isinstance(user, AuthenticatedClient) and user.id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your orders",
        )

    client = await clients_service.get_client(client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    return await service.list_by_client(
        client_id=client_id, statuses=parse_order_statuses(statuses)
    )


@router.get(
    "/{client_id}/retail-point/orders",
    response_model=list[OrderResponse],
)
async def list_client_retail_point_orders(
    client_id: UUID,
    user: Annotated[
        AuthenticatedEmployee | AuthenticatedClient, Depends(get_current_user)
    ],
    service: Annotated[OrdersService, Depends(get_orders_service)],
    clients_service: Annotated[ClientsService, Depends(get_clients_service)],
    statuses: Annotated[list[str] | None, Query()] = None,
):
    if isinstance(user, AuthenticatedClient) and user.id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your orders",
        )

    client = await clients_service.get_client(client_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    return await service.list_by_client_retail_point(
        client_id=client_id, statuses=parse_order_statuses(statuses)
    )


@router.get(
    "",
    response_model=list[ClientResponse],
    dependencies=[Depends(allow_all_staff)],
)
async def list_clients(
    service: Annotated[ClientsService, Depends(get_clients_service)],
):
    return await service.list_clients()


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
    dependencies=[Depends(allow_all_staff)],
)
async def update_client(
    client_id: UUID,
    dto: ClientUpdate,
    service: Annotated[ClientsService, Depends(get_clients_service)],
):
    try:
        app_dto = ClientUpdateDTO(
            phone=dto.phone,
            full_name=dto.full_name,
            telegram_chat_id=dto.telegram_chat_id,
            is_active=dto.is_active,
        )
        return await service.update_client(client_id, app_dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(allow_all_staff)],
)
async def delete_client(
    client_id: UUID, service: Annotated[ClientsService, Depends(get_clients_service)]
):
    await service.delete_client(client_id)
