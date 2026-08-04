from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.media import MediaFile
from app.domain.entities.visit_media import VisitMedia
from app.domain.entities.visits import Visit
from app.domain.enums import MediaBucket
from app.infrastructure.postgres.repos.media_objects import (
    PostgresMediaObjectRepository,
)
from app.infrastructure.postgres.repos.visit_media import PostgresVisitMediaRepository
from app.infrastructure.postgres.repos.visits import PostgresVisitRepository


@pytest.mark.asyncio
async def test_visit_media_repo_operations(session: AsyncSession):
    visit_repo = PostgresVisitRepository(session)
    media_repo = PostgresMediaObjectRepository(session)
    repo = PostgresVisitMediaRepository(session)

    visit = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    await visit_repo.add(visit)

    media = MediaFile(
        bucket=MediaBucket.VISITS,
        original_object_name="test.jpg",
        original_filename="test.jpg",
        content_type="image/jpeg",
        size=100,
        uploaded_by=uuid4(),
    )
    await media_repo.add(media)
    await session.commit()

    vm = VisitMedia(visit_id=visit.id, media_id=media.id)
    await repo.add(vm)
    await session.commit()

    found = await repo.get(visit.id, media.id)
    assert found is not None
    assert found.visit_id == visit.id
    assert found.media_id == media.id

    list_vm = await repo.list_by_visit(visit.id)
    assert len(list_vm) == 1

    assert await repo.exists_by(id=vm.id) is True

    await repo.delete(vm)
    await session.commit()

    deleted = await repo.get(visit.id, media.id)
    assert deleted is None
