from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user, get_media_service
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.media import MediaFile
from app.infrastructure.postgres.models.enums import EmployeeRole
from app.main import app


@pytest.fixture
def mock_service():
    return AsyncMock()


@pytest.fixture
def mock_admin_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000000",
        role=EmployeeRole.ADMIN,
        full_name="Mock Admin",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_service, mock_admin_employee):
    app.dependency_overrides[get_media_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _media_response():
    return MediaFile(
        id=uuid4(),
        bucket="retail-point-images",
        original_object_name="abc123.webp",
        thumbnail_object_name="abc123_thumb.webp",
        content_type="image/webp",
        size=1024,
        uploaded_by=uuid4(),
    )


# --- POST /api/v1/media/upload ---


@pytest.mark.asyncio
async def test_upload_media_success(client, mock_service, mock_admin_employee):
    media = _media_response()
    mock_service.upload.return_value = media

    resp = await client.post(
        "/api/v1/media/upload",
        files={"file": ("test.jpg", b"fake-image-data", "image/jpeg")},
        params={"bucket": "retail-point-images"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["original_object_name"] == "abc123.webp"
    assert data["content_type"] == "image/webp"
    assert data["size"] == 1024


@pytest.mark.asyncio
async def test_upload_media_empty_file(client, mock_service):
    resp = await client.post(
        "/api/v1/media/upload",
        files={"file": ("empty.jpg", b"", "image/jpeg")},
        params={"bucket": "retail-point-images"},
    )
    assert resp.status_code == 400
    assert "File is empty" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_upload_media_invalid_type(client, mock_service):
    mock_service.upload.side_effect = ValueError("Unsupported image type.")

    resp = await client.post(
        "/api/v1/media/upload",
        files={"file": ("test.pdf", b"fake-pdf-data", "application/pdf")},
        params={"bucket": "retail-point-images"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_upload_media_too_large(client, mock_service):
    mock_service.upload.side_effect = ValueError("Image is too large.")

    resp = await client.post(
        "/api/v1/media/upload",
        files={"file": ("large.jpg", b"x" * (16 * 1024 * 1024), "image/jpeg")},
        params={"bucket": "retail-point-images"},
    )
    assert resp.status_code == 400


# --- GET /api/v1/media/{media_id}/content ---


@pytest.mark.asyncio
async def test_get_media_content_success(client, mock_service):
    mock_service.get_content.return_value = (b"image-data", "image/webp")

    resp = await client.get(f"/api/v1/media/{uuid4()}/content")
    assert resp.status_code == 200
    assert resp.content == b"image-data"


@pytest.mark.asyncio
async def test_get_media_content_not_found(client, mock_service):
    from app.core.exceptions import MediaNotFoundError

    mock_service.get_content.side_effect = MediaNotFoundError()

    resp = await client.get(f"/api/v1/media/{uuid4()}/content")
    assert resp.status_code == 404


# --- GET /api/v1/media/{media_id}/thumbnail ---


@pytest.mark.asyncio
async def test_get_media_thumbnail_success(client, mock_service):
    mock_service.get_thumbnail.return_value = (b"thumb-data", "image/webp")

    resp = await client.get(f"/api/v1/media/{uuid4()}/thumbnail")
    assert resp.status_code == 200
    assert resp.content == b"thumb-data"


@pytest.mark.asyncio
async def test_get_media_thumbnail_not_found(client, mock_service):
    from app.core.exceptions import MediaNotFoundError

    mock_service.get_thumbnail.side_effect = MediaNotFoundError()

    resp = await client.get(f"/api/v1/media/{uuid4()}/thumbnail")
    assert resp.status_code == 404
