from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.media import MediaFile
from app.domain.enums import MediaBucket
from app.infrastructure.postgres.repos.media_objects import PostgresMediaObjectRepository


@pytest.mark.asyncio
async def test_media_object_repo_operations(session: AsyncSession):
    repo = PostgresMediaObjectRepository(session)
    uploader_id = uuid4()

    media = MediaFile(
        bucket=MediaBucket.RETAIL_POINTS,
        original_object_name="orig/path.jpg",
        original_filename="path.jpg",
        content_type="image/jpeg",
        size=1024,
        uploaded_by=uploader_id,
    )

    await repo.add(media)
    await session.commit()

    found = await repo.get_by_id(media.id)
    assert found is not None
    assert found.bucket == MediaBucket.RETAIL_POINTS
    assert found.size == 1024

    assert await repo.exists_by(id=media.id) is True

    media.size = 2048
    await repo.update(media)
    await session.commit()

    updated = await repo.get_by_id(media.id)
    assert updated.size == 2048

    await repo.delete(media)
    await session.commit()

    deleted = await repo.get_by_id(media.id)
    assert deleted is None
