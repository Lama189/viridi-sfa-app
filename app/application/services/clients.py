from uuid import UUID

from app.domain.entities.clients import Client
from app.core.extensions import UserNotFoundError
from app.core.security import SecurityUtils

from app.application.interfaces.uow import IUnitOfWork
from app.application.interfaces.cache.clients_cache import IClientsCacheRepository
from app.api.v1.schemas.tokens import TokenResponseDTO
from app.api.v1.schemas.clients import (
    ClientCreate, 
    ClientUpdate, 
    ClientCachedDTO, 
    ClientLoginDTO, 
    ClientConfirm,
    ClientResponse,
    ClientWithTokensResponse
)

from app.infrastructure.context import client_id_ctx_var


class ClientsService:

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_client(self, dto: ClientCreate) -> Client:
        if await self._uow.clients.exists_by(phone=dto.phone):
            raise ValueError(f"A client with phone number '{dto.phone}' already exists.")

        client = Client(
            phone=dto.phone,
            full_name=dto.full_name,
            telegram_chat_id=dto.telegram_chat_id,
        )

        await self._uow.clients.add(client)
        await self._uow.commit()
        return client

    async def get_client(self, client_id: UUID) -> Client | None:
        return await self._uow.clients.get_by_id(client_id)

    async def get_client_by_phone(self, phone: str) -> Client | None:
        return await self._uow.clients.get_by_phone(phone)

    async def list_clients(self, only_active: bool = True) -> list[Client]:
        return await self._uow.clients.list_all(only_active)

    async def update_client(self, client_id: UUID, dto: ClientUpdate) -> Client:
        client = await self._uow.clients.get_by_id(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        if dto.phone is not None:
            existing = await self._uow.clients.get_by_phone(dto.phone)
            if existing and existing.id != client_id:
                raise ValueError(f"Phone '{dto.phone}' is already in use")
            client.phone = dto.phone

        if dto.full_name is not None:
            client.full_name = dto.full_name

        if dto.telegram_chat_id is not None:
            client.telegram_chat_id = dto.telegram_chat_id

        if dto.is_active is not None:
            client.is_active = bool(dto.is_active)

        await self._uow.clients.update(client)
        await self._uow.commit()
        return client

    async def delete_client(self, client_id: UUID) -> None:
        client = await self._uow.clients.get_by_id(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        await self._uow.clients.delete(client)
        await self._uow.commit()


class ClientsAuthService:

    def __init__(self, uow: IUnitOfWork, cache: IClientsCacheRepository) -> None:
        self._uow = uow
        self._cache = cache

    async def _generate_auth_session(self, client: Client) -> TokenResponseDTO:
        client_id_str = str(client.id)
        client_id_ctx_var.set(client_id_str)

        payload = {
            "sub": client_id_str, 
            "telegram_chat_id": client.telegram_chat_id,
            "user_type": "client" 
        }
        access_token = SecurityUtils.generate_access_token(payload)
        refresh_token = SecurityUtils.generate_refresh_token(payload)

        await self._cache.set_refresh_token(
            client_id=client_id_str,
            token=refresh_token,
        )

        await self._cache.set_user(
            client_id=client_id_str,
            user=ClientCachedDTO.model_validate(client),
        )

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=client.id
        )
    
    async def login(self, dto: ClientLoginDTO) -> TokenResponseDTO:
        client = await self._uow.clients.get_by_phone(dto.phone)
        if not client:
            raise UserNotFoundError()
        
        if dto.telegram_chat_id is not None and client.telegram_chat_id != dto.telegram_chat_id:
            client.telegram_chat_id = dto.telegram_chat_id
            await self._uow.clients.update(client)
            await self._uow.commit()
            
        return await self._generate_auth_session(client)
    
    async def confirm(self, dto: ClientConfirm) -> ClientWithTokensResponse:
        client = await self._uow.clients.get_by_phone(dto.phone)
        if not client:
            raise UserNotFoundError()
        
        client.telegram_chat_id = dto.telegram_chat_id
        if dto.full_name:
            client.full_name = dto.full_name

        await self._uow.clients.update(client)
        await self._uow.commit()
        
        tokens = await self._generate_auth_session(client)

        return ClientWithTokensResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            client=ClientResponse.model_validate(client)
        )
    
    async def refresh(self, refresh_token: str) -> TokenResponseDTO:
        payload = SecurityUtils.verify_token(refresh_token, expected_type="refresh")
        client_id = payload.get("sub")

        client_id_ctx_var.set(str(client_id))

        stored_token = await self._cache.get_refresh_token(client_id)
        if not stored_token or stored_token != refresh_token:
            raise ValueError("Refresh token is invalid")
        
        new_access = SecurityUtils.generate_access_token({"sub": client_id})

        return TokenResponseDTO(
            access_token=new_access,
            refresh_token=refresh_token,
            user_id=client_id
        )
    
    async def logout(self, client_id: str) -> None:
        await self._cache.delete_refresh_token(client_id)
        await self._cache.delete_user(client_id)