from uuid import UUID

from app.api.v1.schemas.clients import (
    ClientLoginDTO,
    ClientRegisterRequest,
    ClientResponse,
    ClientTelegramLoginRequest,
    ClientUpdate,
    ClientWithTokensResponse,
)
from app.api.v1.schemas.tokens import TokenResponseDTO
from app.application.interfaces.cache.clients_cache import IClientsCacheRepository
from app.application.interfaces.services.invite_codes import IClientInviteCodesService
from app.application.interfaces.services.retail_point_members import (
    IRetailPointMembersService,
)
from app.application.interfaces.uow import IUnitOfWork
from app.core.config import get_settings
from app.core.context import client_id_ctx_var
from app.core.exceptions import UserNotActiveError, UserNotFoundError
from app.core.observability.metrics import client_operations_total
from app.core.security import SecurityUtils
from app.domain.entities.auth import AuthenticatedClient
from app.domain.entities.clients import Client

settings = get_settings()


class ClientsService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def get_client(self, client_id: UUID) -> Client | None:
        return await self._uow.clients.get_by_id(client_id)

    async def get_client_by_phone(self, phone: str) -> Client | None:
        return await self._uow.clients.get_by_phone(phone)

    async def get_by_telegram_chat_id(self, telegram_chat_id: int) -> Client | None:
        return await self._uow.clients.get_by_telegram_chat_id(telegram_chat_id)

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
        client_operations_total.labels(action="update").inc()
        return client

    async def delete_client(self, client_id: UUID) -> None:
        client = await self._uow.clients.get_by_id(client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        await self._uow.clients.delete(client)
        await self._uow.commit()
        client_operations_total.labels(action="delete").inc()


class ClientsAuthService:
    def __init__(
        self,
        uow: IUnitOfWork,
        cache: IClientsCacheRepository,
        invite_codes: IClientInviteCodesService,
        memberships: IRetailPointMembersService,
    ) -> None:
        self._uow = uow
        self._cache = cache
        self._invite_codes = invite_codes
        self._memberships = memberships

    async def _generate_auth_session(
        self,
        client: Client,
    ) -> TokenResponseDTO:
        client_id = str(client.id)
        client_id_ctx_var.set(client_id)

        payload = {
            "sub": client_id,
            "telegram_chat_id": client.telegram_chat_id,
            "user_type": "client",
        }

        access_token = SecurityUtils.generate_access_token(payload)
        refresh_token = SecurityUtils.generate_refresh_token(payload)

        await self._cache.set_refresh_token(
            client_id=client_id,
            token=refresh_token,
        )

        await self._cache.set_user(
            client_id=client_id,
            user=AuthenticatedClient.from_entity(client),
        )

        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            user_id=client.id,
        )

    async def register(
        self,
        dto: ClientRegisterRequest,
    ) -> ClientWithTokensResponse:
        existing_client = await self._uow.clients.get_by_phone(dto.phone)

        if existing_client is not None:
            if dto.telegram_chat_id is not None:
                existing_client.telegram_chat_id = dto.telegram_chat_id
            if dto.full_name and not existing_client.full_name:
                existing_client.full_name = dto.full_name

            await self._uow.clients.update(existing_client)

            if dto.invite_code:
                try:
                    invite = await self._invite_codes.activate(
                        dto.invite_code,
                        existing_client.id,
                    )
                    await self._memberships.join(
                        invite.retail_point_id,
                        existing_client.id,
                    )
                except Exception:  # noqa: BLE001, S110
                    pass

            await self._uow.commit()

            tokens = await self._generate_auth_session(existing_client)
            client_operations_total.labels(action="register").inc()

            return ClientWithTokensResponse(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                client=ClientResponse.model_validate(existing_client),
            )

        client = Client(
            phone=dto.phone,
            full_name=dto.full_name,
            telegram_chat_id=dto.telegram_chat_id,
            is_active=True,
        )

        await self._uow.clients.add(client)

        invite = await self._invite_codes.activate(
            dto.invite_code,
            client.id,
        )

        await self._memberships.join(
            invite.retail_point_id,
            client.id,
        )

        await self._uow.commit()

        tokens = await self._generate_auth_session(client)
        client_operations_total.labels(action="register").inc()

        return ClientWithTokensResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            client=ClientResponse.model_validate(client),
        )

    async def login(
        self,
        dto: ClientLoginDTO,
    ) -> TokenResponseDTO:
        client = await self._uow.clients.get_by_phone(dto.phone)
        if client is None:
            raise UserNotFoundError()

        if not client.is_active:
            raise UserNotActiveError()

        if (
            dto.telegram_chat_id is not None
            and client.telegram_chat_id != dto.telegram_chat_id
        ):
            client.telegram_chat_id = dto.telegram_chat_id
            await self._uow.clients.update(client)
            await self._uow.commit()

        tokens = await self._generate_auth_session(client)
        client_operations_total.labels(action="login").inc()
        return tokens

    async def telegram_login(
        self,
        dto: ClientTelegramLoginRequest,
    ) -> ClientWithTokensResponse:
        try:
            parsed_data = SecurityUtils.verify_telegram_init_data(
                dto.init_data,
                settings.telegram_bot_token,
            )
        except ValueError as e:
            raise ValueError(f"Telegram authentication failed: {e}")

        user_data = parsed_data.get("user")
        if not isinstance(user_data, dict) or "id" not in user_data:
            raise ValueError("Invalid initData: missing user information")

        telegram_chat_id = int(user_data["id"])

        client = await self._uow.clients.get_by_telegram_chat_id(telegram_chat_id)
        if client is None:
            raise UserNotFoundError()

        if not client.is_active:
            raise UserNotActiveError()

        tokens = await self._generate_auth_session(client)
        client_operations_total.labels(action="telegram_login").inc()

        return ClientWithTokensResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            client=ClientResponse.model_validate(client),
        )

    async def refresh(
        self,
        refresh_token: str,
    ) -> TokenResponseDTO:
        payload = SecurityUtils.verify_token(
            refresh_token,
            expected_type="refresh",
        )

        client_id = str(payload["sub"])
        client_id_ctx_var.set(client_id)

        stored = await self._cache.get_refresh_token(client_id)
        if stored != refresh_token:
            raise ValueError("Refresh token is invalid")

        access = SecurityUtils.generate_access_token(
            {
                "sub": client_id,
                "user_type": "client",
            }
        )

        client_operations_total.labels(action="refresh").inc()

        return TokenResponseDTO(
            access_token=access,
            refresh_token=refresh_token,
            user_id=UUID(client_id),
        )

    async def logout(
        self,
        client_id: str,
    ) -> None:
        await self._cache.delete_refresh_token(client_id)
        await self._cache.delete_user(client_id)
        client_operations_total.labels(action="logout").inc()
