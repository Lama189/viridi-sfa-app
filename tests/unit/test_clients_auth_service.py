from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.v1.schemas.clients import ClientLoginDTO, ClientConfirm
from app.application.services.clients import ClientsAuthService
from app.core.extensions import UserNotFoundError
from app.domain.entities.clients import Client


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.clients = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_cache():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_cache):
    return ClientsAuthService(mock_uow, mock_cache)


# --- login ---

@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.generate_access_token", return_value="access_tok")
@patch("app.application.services.clients.SecurityUtils.generate_refresh_token", return_value="refresh_tok")
async def test_login_success(mock_refresh, mock_access, service, mock_uow, mock_cache):
    uid = uuid4()
    client = Client(phone="+998901234567", full_name="Test", id=uid)
    mock_uow.clients.get_by_phone.return_value = client

    dto = ClientLoginDTO(phone="+998901234567")
    result = await service.login(dto)

    assert result.access_token == "access_tok"
    assert result.refresh_token == "refresh_tok"
    assert result.user_id == uid
    mock_cache.set_refresh_token.assert_awaited_once()
    mock_cache.set_user.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_user_not_found(service, mock_uow):
    mock_uow.clients.get_by_phone.return_value = None

    dto = ClientLoginDTO(phone="+998900000000")
    with pytest.raises(UserNotFoundError):
        await service.login(dto)


@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.generate_access_token", return_value="access_tok")
@patch("app.application.services.clients.SecurityUtils.generate_refresh_token", return_value="refresh_tok")
async def test_login_updates_telegram_chat_id(mock_refresh, mock_access, service, mock_uow, mock_cache):
    uid = uuid4()
    client = Client(phone="+998901234567", full_name="Test", id=uid, telegram_chat_id=None)
    mock_uow.clients.get_by_phone.return_value = client

    dto = ClientLoginDTO(phone="+998901234567", telegram_chat_id=111111)
    await service.login(dto)

    assert client.telegram_chat_id == 111111
    mock_uow.clients.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.generate_access_token", return_value="access_tok")
@patch("app.application.services.clients.SecurityUtils.generate_refresh_token", return_value="refresh_tok")
async def test_login_no_telegram_update_when_same(mock_refresh, mock_access, service, mock_uow, mock_cache):
    uid = uuid4()
    client = Client(phone="+998901234567", full_name="Test", id=uid, telegram_chat_id=222222)
    mock_uow.clients.get_by_phone.return_value = client

    dto = ClientLoginDTO(phone="+998901234567", telegram_chat_id=222222)
    await service.login(dto)

    mock_uow.clients.update.assert_not_awaited()


# --- confirm ---

@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.generate_access_token", return_value="access_tok")
@patch("app.application.services.clients.SecurityUtils.generate_refresh_token", return_value="refresh_tok")
async def test_confirm_success(mock_refresh, mock_access, service, mock_uow, mock_cache):
    uid = uuid4()
    client = Client(phone="+998901234567", full_name="Old", id=uid)
    mock_uow.clients.get_by_phone.return_value = client

    dto = ClientConfirm(phone="+998901234567", telegram_chat_id=333333, full_name="New Name")
    result = await service.confirm(dto)

    assert client.telegram_chat_id == 333333
    assert client.full_name == "New Name"
    assert result.access_token == "access_tok"
    assert result.client.full_name == "New Name"


@pytest.mark.asyncio
async def test_confirm_not_found(service, mock_uow):
    mock_uow.clients.get_by_phone.return_value = None

    dto = ClientConfirm(phone="+998900000000", telegram_chat_id=123, full_name=None)
    with pytest.raises(UserNotFoundError):
        await service.confirm(dto)


@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.generate_access_token", return_value="access_tok")
@patch("app.application.services.clients.SecurityUtils.generate_refresh_token", return_value="refresh_tok")
async def test_confirm_without_full_name(mock_refresh, mock_access, service, mock_uow, mock_cache):
    uid = uuid4()
    client = Client(phone="+998901234567", full_name="Keep", id=uid)
    mock_uow.clients.get_by_phone.return_value = client

    dto = ClientConfirm(phone="+998901234567", telegram_chat_id=444444, full_name=None)
    await service.confirm(dto)

    assert client.full_name == "Keep"
    assert client.telegram_chat_id == 444444


# --- refresh ---

@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.verify_token")
@patch("app.application.services.clients.SecurityUtils.generate_access_token", return_value="new_access")
async def test_refresh_success(mock_access, mock_verify, service, mock_uow, mock_cache):
    uid = uuid4()
    mock_verify.return_value = {"sub": str(uid)}
    mock_cache.get_refresh_token.return_value = "old_refresh"

    result = await service.refresh("old_refresh")

    assert result.access_token == "new_access"
    assert result.refresh_token == "old_refresh"
    mock_cache.get_refresh_token.assert_awaited_once_with(str(uid))


@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.verify_token")
async def test_refresh_invalid_token_in_cache(mock_verify, service, mock_uow, mock_cache):
    uid = uuid4()
    mock_verify.return_value = {"sub": str(uid)}
    mock_cache.get_refresh_token.return_value = None

    with pytest.raises(ValueError, match="Refresh token is invalid"):
        await service.refresh("bad_refresh")


@pytest.mark.asyncio
@patch("app.application.services.clients.SecurityUtils.verify_token")
async def test_refresh_token_mismatch(mock_verify, service, mock_uow, mock_cache):
    uid = uuid4()
    mock_verify.return_value = {"sub": str(uid)}
    mock_cache.get_refresh_token.return_value = "stored_token"

    with pytest.raises(ValueError, match="Refresh token is invalid"):
        await service.refresh("different_token")


# --- logout ---

@pytest.mark.asyncio
async def test_logout(service, mock_cache):
    await service.logout("client-123")

    mock_cache.delete_refresh_token.assert_awaited_once_with("client-123")
    mock_cache.delete_user.assert_awaited_once_with("client-123")
