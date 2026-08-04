from uuid import UUID

from app.application.interfaces.services.visit_media import IVisitMediaService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import (
    MediaNotFoundError,
    VisitMediaAlreadyAttachedError,
    VisitMediaNotFoundError,
    VisitNotFoundError,
)
from app.domain.entities.visit_media import VisitMedia


class VisitMediaService(IVisitMediaService):
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def attach(self, visit_id: UUID, media_id: UUID) -> VisitMedia:
        if not await self._uow.visits.exists_by(id=visit_id):
            raise VisitNotFoundError()

        if not await self._uow.media_objects.exists_by(id=media_id):
            raise MediaNotFoundError()

        if await self._uow.visit_media.exists_by(visit_id=visit_id, media_id=media_id):
            raise VisitMediaAlreadyAttachedError()

        media = VisitMedia(visit_id, media_id)
        await self._uow.visit_media.add(media)

        return media

    async def detach(self, visit_id: UUID, media_id: UUID) -> None:
        media = await self._uow.visit_media.get(visit_id, media_id)
        if not media:
            raise VisitMediaNotFoundError()

        await self._uow.visit_media.delete(media)

    async def list_media(self, visit_id: UUID) -> list[VisitMedia]:
        return await self._uow.visit_media.list_by_visit(visit_id)
