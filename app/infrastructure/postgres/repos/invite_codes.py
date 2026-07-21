from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.invite_codes import IInviteCodeRepository
from app.domain.entities.invite_codes import ClientInviteCode
from app.infrastructure.postgres.models.invite_codes import RetailPointInviteCode as InviteCodeModel


class PostgresInviteCodeRepository(IInviteCodeRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, invite_code: ClientInviteCode) -> None:
        model = self._to_model(invite_code)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, invite_code_id: UUID) -> ClientInviteCode | None:
        result = await self._session.execute(
            select(InviteCodeModel).where(InviteCodeModel.id == invite_code_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_retail_point(self, retail_point_id: UUID) -> list[ClientInviteCode]:
        result = await self._session.execute(
            select(InviteCodeModel).where(
                InviteCodeModel.retail_point_id == retail_point_id
            )
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_by_code_hash(self, code_hash: str) -> ClientInviteCode | None:
        result = await self._session.execute(
            select(InviteCodeModel).where(InviteCodeModel.code_hash == code_hash)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def exists(self, retail_point_id: UUID, code_hash: str) -> bool:
        stmt = select(
            select(InviteCodeModel).where(
                InviteCodeModel.retail_point_id == retail_point_id,
                InviteCodeModel.code_hash == code_hash,
            ).exists()
        )
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def update(self, invite_code: ClientInviteCode) -> None:
        await self._session.execute(
            update(InviteCodeModel)
            .where(InviteCodeModel.id == invite_code.id)
            .values(
                code=invite_code.code_hash,
                is_active=invite_code.is_active,
                last_activated_client_id=invite_code.last_activated_client_id,
                last_activated_at=invite_code.last_activated_at,
            )
        )
        await self._session.flush()

    def _to_domain(self, model: InviteCodeModel) -> ClientInviteCode:
        return ClientInviteCode(
            id=model.id,
            retail_point_id=model.retail_point_id,
            code_hash=model.code_hash,
            created_by_employee_id=model.created_by_employee_id,
            is_active=model.is_active,
            last_activated_client_id=model.last_activated_client_id,
            last_activated_at=model.last_activated_at,
            created_at=model.created_at,
            updated_at=model.created_at,
        )

    def _to_model(self, invite_code: ClientInviteCode) -> InviteCodeModel:
        return InviteCodeModel(
            id=invite_code.id,
            retail_point_id=invite_code.retail_point_id,
            code=invite_code.code_hash,
            created_by_employee_id=invite_code.created_by_employee_id,
            is_active=invite_code.is_active,
            last_activated_client_id=invite_code.last_activated_client_id,
            last_activated_at=invite_code.last_activated_at,
            created_at=invite_code.created_at,
        )
