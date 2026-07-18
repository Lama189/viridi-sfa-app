from uuid import UUID

from app.domain.entities.clients import Client

from app.application.interfaces.uow import IUnitOfWork
from app.api.v1.schemas.clients import ClientCreate, ClientUpdate


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
