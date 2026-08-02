from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.clients import IClientRepository
from app.domain.entities.clients import Client
from app.infrastructure.postgres.models.clients import Client as ClientModel


class PostgresClientRepository(IClientRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, client: Client) -> None:
        model = self._to_model(client)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, client_id: UUID) -> Client | None:
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.id == client_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_phone(self, phone: str) -> Client | None:
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.phone == phone)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_telegram_chat_id(self, telegram_chat_id: int) -> Client | None:
        result = await self._session.execute(
            select(ClientModel).where(ClientModel.telegram_chat_id == telegram_chat_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)


    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(ClientModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_all(self, only_active: bool = True) -> list[Client]:
        stmt = select(ClientModel)
        if only_active:
            stmt = stmt.where(ClientModel.is_active.is_(True))

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, client: Client) -> None:
        await self._session.execute(
            update(ClientModel)
            .where(ClientModel.id == client.id)
            .values(
                phone=client.phone,
                full_name=client.full_name,
                telegram_chat_id=client.telegram_chat_id,
                is_active=client.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, client: Client) -> None:
        await self._session.execute(
            sa_delete(ClientModel).where(ClientModel.id == client.id)
        )
        await self._session.flush()

    def _to_domain(self, model: ClientModel) -> Client:
        return Client(
            id=model.id,
            phone=model.phone,
            full_name=model.full_name,
            telegram_chat_id=model.telegram_chat_id,
            is_active=model.is_active,
        )

    def _to_model(self, client: Client) -> ClientModel:
        return ClientModel(
            id=client.id,
            phone=client.phone,
            full_name=client.full_name,
            telegram_chat_id=client.telegram_chat_id,
            is_active=client.is_active,
        )
