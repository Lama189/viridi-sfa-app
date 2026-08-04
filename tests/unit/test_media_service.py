from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.services.media import MediaService
from app.domain.enums import MediaBucket


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.media_objects = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_storage():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_storage):
    return MediaService(mock_uow, mock_storage)


def _make_jpeg_bytes():
    """Create minimal valid JPEG bytes for testing."""
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (100, 100), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# --- upload ---

@pytest.mark.asyncio
async def test_upload_success(service, mock_uow, mock_storage):

    mock_uow.media_objects.add.return_value = None
    mock_storage.upload.return_value = None

    data = _make_jpeg_bytes()
    result = await service.upload(
        uploaded_by=uuid4(),
        bucket=MediaBucket.VISITS,
        data=data,
        content_type="image/jpeg",
        filename="test.jpg",
    )

    assert result.bucket == MediaBucket.VISITS.value
    assert result.content_type == "image/webp"
    assert result.original_filename == "test.jpg"
    assert mock_storage.upload.await_count == 2
    mock_uow.media_objects.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_upload_unsupported_content_type(service):
    with pytest.raises(ValueError, match="Unsupported image type"):
        await service.upload(
            uploaded_by=uuid4(),
            bucket=MediaBucket.VISITS,
            data=b"fake-data",
            content_type="application/pdf",
        )


@pytest.mark.asyncio
async def test_upload_file_too_large(service):
    large_data = b"x" * (16 * 1024 * 1024)
    with pytest.raises(ValueError, match="too large"):
        await service.upload(
            uploaded_by=uuid4(),
            bucket=MediaBucket.VISITS,
            data=large_data,
            content_type="image/jpeg",
        )


@pytest.mark.asyncio
async def test_upload_invalid_image(service):
    with pytest.raises(ValueError, match="Invalid image"):
        await service.upload(
            uploaded_by=uuid4(),
            bucket=MediaBucket.VISITS,
            data=b"not-an-image",
            content_type="image/jpeg",
        )


@pytest.mark.asyncio
async def test_upload_with_prefix(service, mock_uow, mock_storage):
    mock_uow.media_objects.add.return_value = None
    mock_storage.upload.return_value = None

    data = _make_jpeg_bytes()
    result = await service.upload(
        uploaded_by=uuid4(),
        bucket=MediaBucket.VISITS,
        data=data,
        content_type="image/jpeg",
        prefix="visit-123",
    )

    assert "visit-123/original/" in result.original_object_name
    assert "visit-123/thumbnail/" in result.thumbnail_object_name


# --- get_content ---

@pytest.mark.asyncio
async def test_get_content_success(service, mock_uow, mock_storage):
    media_id = uuid4()
    mock_uow.media_objects.get_by_id.return_value = MagicMock(
        bucket="visits",
        original_object_name="abc.webp",
        content_type="image/webp",
    )
    mock_storage.download.return_value = (b"image-data", "image/webp")

    data, content_type = await service.get_content(media_id)

    assert data == b"image-data"
    assert content_type == "image/webp"
    mock_storage.download.assert_awaited_once_with("visits", "abc.webp")


@pytest.mark.asyncio
async def test_get_content_not_found(service, mock_uow):
    from app.core.exceptions import MediaNotFoundError

    mock_uow.media_objects.get_by_id.return_value = None

    with pytest.raises(MediaNotFoundError):
        await service.get_content(uuid4())


# --- get_thumbnail ---

@pytest.mark.asyncio
async def test_get_thumbnail_success(service, mock_uow, mock_storage):
    media_id = uuid4()
    mock_uow.media_objects.get_by_id.return_value = MagicMock(
        bucket="visits",
        thumbnail_object_name="abc_thumb.webp",
        content_type="image/webp",
    )
    mock_storage.download.return_value = (b"thumb-data", "image/webp")

    data, content_type = await service.get_thumbnail(media_id)

    assert data == b"thumb-data"
    assert content_type == "image/webp"
    mock_storage.download.assert_awaited_once_with("visits", "abc_thumb.webp")


@pytest.mark.asyncio
async def test_get_thumbnail_not_found(service, mock_uow):
    from app.core.exceptions import MediaNotFoundError

    mock_uow.media_objects.get_by_id.return_value = None

    with pytest.raises(MediaNotFoundError):
        await service.get_thumbnail(uuid4())
