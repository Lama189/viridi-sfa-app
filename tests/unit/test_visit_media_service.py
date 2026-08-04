from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.visit_media import VisitMediaService
from app.core.exceptions import (
    VisitNotFoundError,
    MediaNotFoundError,
    VisitMediaNotFoundError,
    VisitMediaAlreadyAttachedError,
)


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.visits = AsyncMock()
    uow.media_objects = AsyncMock()
    uow.visit_media = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return VisitMediaService(mock_uow)


# --- attach ---

@pytest.mark.asyncio
async def test_attach_success(service, mock_uow):
    visit_id = uuid4()
    media_id = uuid4()

    mock_uow.visits.exists_by.return_value = True
    mock_uow.media_objects.exists_by.return_value = True
    mock_uow.visit_media.exists_by.return_value = False
    mock_uow.visit_media.add.return_value = None

    result = await service.attach(visit_id, media_id)

    assert result.visit_id == visit_id
    assert result.media_id == media_id
    mock_uow.visit_media.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_attach_visit_not_found(service, mock_uow):
    mock_uow.visits.exists_by.return_value = False

    with pytest.raises(VisitNotFoundError):
        await service.attach(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_attach_media_not_found(service, mock_uow):
    mock_uow.visits.exists_by.return_value = True
    mock_uow.media_objects.exists_by.return_value = False

    with pytest.raises(MediaNotFoundError):
        await service.attach(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_attach_already_attached(service, mock_uow):
    mock_uow.visits.exists_by.return_value = True
    mock_uow.media_objects.exists_by.return_value = True
    mock_uow.visit_media.exists_by.return_value = True

    with pytest.raises(VisitMediaAlreadyAttachedError):
        await service.attach(uuid4(), uuid4())


# --- detach ---

@pytest.mark.asyncio
async def test_detach_success(service, mock_uow):
    from app.domain.entities.visit_media import VisitMedia

    visit_id = uuid4()
    media_id = uuid4()
    media = VisitMedia(visit_id, media_id)

    mock_uow.visit_media.get.return_value = media
    mock_uow.visit_media.delete.return_value = None

    await service.detach(visit_id, media_id)

    mock_uow.visit_media.delete.assert_awaited_once_with(media)


@pytest.mark.asyncio
async def test_detach_not_found(service, mock_uow):
    mock_uow.visit_media.get.return_value = None

    with pytest.raises(VisitMediaNotFoundError):
        await service.detach(uuid4(), uuid4())


# --- list_media ---

@pytest.mark.asyncio
async def test_list_media(service, mock_uow):
    visit_id = uuid4()
    mock_uow.visit_media.list_by_visit.return_value = []

    result = await service.list_media(visit_id)

    assert result == []
    mock_uow.visit_media.list_by_visit.assert_awaited_once_with(visit_id)
