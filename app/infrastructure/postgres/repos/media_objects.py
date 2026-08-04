from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.media_objects import IMediaObjectRepository
from app.domain.entities.media import MediaFile
from app.infrastructure.postgres.models.media_objects import (
    MediaObject as MediaObjectModel,
)


class PostgresMediaObjectRepository(IMediaObjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, media: MediaFile) -> None:
        model = self._to_model(media)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, media_id: UUID) -> MediaFile | None:
        result = await self._session.execute(
            select(MediaObjectModel).where(MediaObjectModel.id == media_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(MediaObjectModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def update(self, media: MediaFile) -> None:
        await self._session.execute(
            update(MediaObjectModel)
            .where(MediaObjectModel.id == media.id)
            .values(
                bucket=media.bucket,
                original_object_name=media.original_object_name,
                thumbnail_object_name=media.thumbnail_object_name,
                content_type=media.content_type,
                size=media.size,
                original_filename=media.original_filename,
                uploaded_by=media.uploaded_by,
            )
        )
        await self._session.flush()

    async def delete(self, media: MediaFile) -> None:
        await self._session.execute(
            sa_delete(MediaObjectModel).where(MediaObjectModel.id == media.id)
        )
        await self._session.flush()

    def _to_domain(self, model: MediaObjectModel) -> MediaFile:
        return MediaFile(
            id=model.id,
            bucket=model.bucket,
            original_object_name=model.original_object_name,
            thumbnail_object_name=model.thumbnail_object_name,
            content_type=model.content_type,
            size=model.size,
            original_filename=model.original_filename,
            uploaded_by=model.uploaded_by,
        )

    def _to_model(self, media: MediaFile) -> MediaObjectModel:
        return MediaObjectModel(
            id=media.id,
            bucket=media.bucket,
            original_object_name=media.original_object_name,
            thumbnail_object_name=media.thumbnail_object_name,
            content_type=media.content_type,
            size=media.size,
            original_filename=media.original_filename,
            uploaded_by=media.uploaded_by,
        )
