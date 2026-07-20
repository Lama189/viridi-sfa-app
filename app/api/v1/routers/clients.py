from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.extensions import UserNotFoundError
from app.application.services.clients import ClientsAuthService, ClientsService
from app.api.dependencies import get_clients_service, get_clients_auth_service, allow_all_staff
from app.api.v1.schemas.clients import (
    ClientCreate, 
    ClientResponse, 
    ClientConfirm, 
    ClientWithTokensResponse
)



router = APIRouter(prefix="/api/v1/clients", tags=["Clients"])


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    response_model=ClientResponse,
    dependencies=[Depends(allow_all_staff)]
)
async def register(
    dto: ClientCreate,
    service: Annotated[ClientsService, Depends(get_clients_service)],
):
    try:
        return await service.create_client(dto) 
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    path="/confirm",
    status_code=status.HTTP_200_OK,
    response_model=ClientWithTokensResponse
)
async def confirm(
    dto: ClientConfirm,
    service: Annotated[ClientsAuthService, Depends(get_clients_auth_service)]
):
    try:
        return await service.confirm(dto)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")