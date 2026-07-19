from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.clients import ClientCreate, ClientUpdate
from app.application.services.clients import ClientsService
from app.domain.entities.clients import Client


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.clients = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return ClientsService(mock_uow)


# --- create_client ---

@pytest.mark.asyncio
async def test_create_client_success(service, mock_uow):
    mock_uow.clients.exists_by.return_value = False

    dto = ClientCreate(phone="+998901234567", full_name="Test Client")
    result = await service.create_client(dto)

    assert result.phone == "+998901234567"
    assert result.full_name == "Test Client"
    assert result.telegram_chat_id is None
    mock_uow.clients.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_client_with_telegram(service, mock_uow):
    mock_uow.clients.exists_by.return_value = False

    dto = ClientCreate(phone="+998901234568", full_name="TG Client", telegram_chat_id=123456789)
    result = await service.create_client(dto)

    assert result.telegram_chat_id == 123456789


@pytest.mark.asyncio
async def test_create_client_duplicate_phone(service, mock_uow):
    mock_uow.clients.exists_by.return_value = True

    dto = ClientCreate(phone="+998901234567", full_name="Dup")
    with pytest.raises(ValueError, match="already exists"):
        await service.create_client(dto)

    mock_uow.clients.add.assert_not_awaited()


# --- get_client ---

@pytest.mark.asyncio
async def test_get_client_found(service, mock_uow):
    uid = uuid4()
    mock_uow.clients.get_by_id.return_value = Client(
        phone="+998901234567", full_name="X", id=uid,
    )

    result = await service.get_client(uid)
    assert result is not None
    assert result.full_name == "X"


@pytest.mark.asyncio
async def test_get_client_not_found(service, mock_uow):
    mock_uow.clients.get_by_id.return_value = None

    result = await service.get_client(uuid4())
    assert result is None


# --- get_client_by_phone ---

@pytest.mark.asyncio
async def test_get_client_by_phone(service, mock_uow):
    mock_uow.clients.get_by_phone.return_value = Client(
        phone="+998901234567", full_name="Phone Client",
    )

    result = await service.get_client_by_phone("+998901234567")
    assert result is not None
    mock_uow.clients.get_by_phone.assert_awaited_once_with("+998901234567")


# --- list_clients ---

@pytest.mark.asyncio
async def test_list_clients(service, mock_uow):
    mock_uow.clients.list_all.return_value = [
        Client(phone="+998901111111", full_name="A"),
        Client(phone="+998902222222", full_name="B"),
    ]

    result = await service.list_clients(only_active=True)
    assert len(result) == 2
    mock_uow.clients.list_all.assert_awaited_once_with(True)


# --- update_client ---

@pytest.mark.asyncio
async def test_update_client_success(service, mock_uow):
    uid = uuid4()
    client = Client(phone="+998905000000", full_name="Old", id=uid)
    mock_uow.clients.get_by_id.return_value = client
    mock_uow.clients.get_by_phone.return_value = None

    dto = ClientUpdate(full_name="New")
    result = await service.update_client(uid, dto)

    assert result.full_name == "New"
    mock_uow.clients.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_client_phone_conflict(service, mock_uow):
    uid = uuid4()
    other_id = uuid4()
    client = Client(phone="+998905000000", full_name="X", id=uid)
    mock_uow.clients.get_by_id.return_value = client
    mock_uow.clients.get_by_phone.return_value = Client(
        phone="+998909999999", full_name="Y", id=other_id,
    )

    dto = ClientUpdate(phone="+998909999999")
    with pytest.raises(ValueError, match="already in use"):
        await service.update_client(uid, dto)


@pytest.mark.asyncio
async def test_update_client_phone_same_owner(service, mock_uow):
    uid = uuid4()
    client = Client(phone="+998909999999", full_name="X", id=uid)
    mock_uow.clients.get_by_id.return_value = client
    mock_uow.clients.get_by_phone.return_value = client

    dto = ClientUpdate(phone="+998909999999")
    result = await service.update_client(uid, dto)
    assert result.phone == "+998909999999"


@pytest.mark.asyncio
async def test_update_client_telegram(service, mock_uow):
    uid = uuid4()
    client = Client(phone="+998905000000", full_name="X", id=uid)
    mock_uow.clients.get_by_id.return_value = client

    dto = ClientUpdate(telegram_chat_id=999999)
    result = await service.update_client(uid, dto)

    assert result.telegram_chat_id == 999999


@pytest.mark.asyncio
async def test_update_client_toggle_active(service, mock_uow):
    uid = uuid4()
    client = Client(phone="+998905000000", full_name="X", id=uid, is_active=True)
    mock_uow.clients.get_by_id.return_value = client

    dto = ClientUpdate(is_active=False)
    result = await service.update_client(uid, dto)

    assert result.is_active is False


@pytest.mark.asyncio
async def test_update_client_not_found(service, mock_uow):
    mock_uow.clients.get_by_id.return_value = None

    dto = ClientUpdate(full_name="X")
    with pytest.raises(ValueError, match="not found"):
        await service.update_client(uuid4(), dto)


# --- delete_client ---

@pytest.mark.asyncio
async def test_delete_client_success(service, mock_uow):
    uid = uuid4()
    mock_uow.clients.get_by_id.return_value = Client(
        phone="+998906000000", full_name="Del", id=uid,
    )

    await service.delete_client(uid)

    mock_uow.clients.delete.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_client_not_found(service, mock_uow):
    mock_uow.clients.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await service.delete_client(uuid4())

    mock_uow.clients.delete.assert_not_awaited()
