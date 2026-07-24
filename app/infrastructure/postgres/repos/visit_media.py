from uuid import UUID

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.visit_media import IVisitMediaRepository
from app.domain.entities.visit_media import VisitMedia
from app.infrastructure.postgres.models.visit_media import VisitMedia as VisitMediaModel


class PostgresVisitMediaRepository(IVisitMediaRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, visit_media: VisitMedia) -> None:
        model = self._to_model(visit_media)
        self._session.add(model)
        await self._session.flush()

    async def get(self, visit_id: UUID, media_id: UUID) -> VisitMedia | None:
        result = await self._session.execute(
            select(VisitMediaModel).where(
                VisitMediaModel.visit_id == visit_id,
                VisitMediaModel.media_id == media_id,
            )
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_visit(self, visit_id: UUID) -> list[VisitMedia]:
        stmt = select(VisitMediaModel).where(
            VisitMediaModel.visit_id == visit_id
        )

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete(self, visit_media: VisitMedia) -> None:
        await self._session.execute(
            sa_delete(VisitMediaModel).where(VisitMediaModel.id == visit_media.id)
        )
        await self._session.flush()

    async def delete_all_for_visit(self, visit_id: UUID) -> None:
        await self._session.execute(
            sa_delete(VisitMediaModel).where(
                VisitMediaModel.visit_id == visit_id
            )
        )
        await self._session.flush()

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(VisitMediaModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    def _to_domain(self, model: VisitMediaModel) -> VisitMedia:
        return VisitMedia(
            id=model.id,
            visit_id=model.visit_id,
            media_id=model.media_id,
            created_at=model.created_at,
        )

    def _to_model(self, visit_media: VisitMedia) -> VisitMediaModel:
        return VisitMediaModel(
            id=visit_media.id,
            visit_id=visit_media.visit_id,
            media_id=visit_media.media_id,
        )
