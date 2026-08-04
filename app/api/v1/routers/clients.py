from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import (
    allow_all_staff,
    get_clients_auth_service,
    get_clients_service,
)
from app.api.v1.schemas.clients import (
    ClientRegisterRequest,
    ClientResponse,
    ClientTelegramLoginRequest,
    ClientUpdate,
    ClientWithTokensResponse,
)
from app.api.v1.schemas.tokens import RefreshTokenDTO, TokenResponseDTO
from app.application.services.clients import (
    ClientsAuthService,
    ClientsService,
)

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
    return await service.register(dto)


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
        return await service.telegram_login(dto)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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
    client = await service.get_by_telegram_chat_id(telegram_chat_id)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    return client


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
    client_id: str,
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
    client_id: str,
    dto: ClientUpdate,
    service: Annotated[ClientsService, Depends(get_clients_service)],
):
    try:
        return await service.update_client(client_id, dto)
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
    client_id: str, service: Annotated[ClientsService, Depends(get_clients_service)]
):
    await service.delete_client(client_id)
