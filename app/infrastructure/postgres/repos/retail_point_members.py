from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.retail_point_members import (
    IRetailPointMemberRepository,
)
from app.domain.entities.retail_point_members import RetailPointMember
from app.infrastructure.postgres.models.clients import Client
from app.infrastructure.postgres.models.retail_point_members import (
    RetailPointMember as RetailPointMemberModel,
)


class PostgresRetailPointMemberRepository(IRetailPointMemberRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, member: RetailPointMember) -> None:
        model = self._to_model(member)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, member_id: UUID) -> RetailPointMember | None:
        result = await self._session.execute(
            select(RetailPointMemberModel).where(RetailPointMemberModel.id == member_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_telegram_id(self, telegram_id: int) -> RetailPointMember | None:
        result = await self._session.execute(
            select(RetailPointMemberModel)
            .join(Client, RetailPointMemberModel.client_id == Client.id)
            .where(Client.telegram_chat_id == telegram_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_client_id(
        self, client_id: UUID
    ) -> list[RetailPointMember]:
        result = await self._session.execute(
            select(RetailPointMemberModel).where(
                RetailPointMemberModel.client_id == client_id
            )
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_retail_point(
        self, retail_point_id: UUID
    ) -> list[RetailPointMember]:
        result = await self._session.execute(
            select(RetailPointMemberModel).where(
                RetailPointMemberModel.retail_point_id == retail_point_id
            )
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_retail_point_and_client(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> RetailPointMember | None:
        result = await self._session.execute(
            select(RetailPointMemberModel).where(
                RetailPointMemberModel.retail_point_id == retail_point_id,
                RetailPointMemberModel.client_id == client_id,
            )
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def exists(self, retail_point_id: UUID, client_id: UUID) -> bool:
        stmt = select(
            select(RetailPointMemberModel)
            .where(
                RetailPointMemberModel.retail_point_id == retail_point_id,
                RetailPointMemberModel.client_id == client_id,
            )
            .exists()
        )
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def update(self, member: RetailPointMember) -> None:
        await self._session.execute(
            update(RetailPointMemberModel)
            .where(RetailPointMemberModel.id == member.id)
            .values(
                retail_point_id=member.retail_point_id,
                client_id=member.client_id,
            )
        )
        await self._session.flush()

    async def delete(self, member: RetailPointMember) -> None:
        await self._session.execute(
            sa_delete(RetailPointMemberModel).where(
                RetailPointMemberModel.id == member.id
            )
        )
        await self._session.flush()

    def _to_domain(self, model: RetailPointMemberModel) -> RetailPointMember:
        return RetailPointMember(
            id=model.id,
            retail_point_id=model.retail_point_id,
            client_id=model.client_id,
            created_at=model.created_at,
        )

    def _to_model(self, member: RetailPointMember) -> RetailPointMemberModel:
        return RetailPointMemberModel(
            id=member.id,
            retail_point_id=member.retail_point_id,
            client_id=member.client_id,
        )
