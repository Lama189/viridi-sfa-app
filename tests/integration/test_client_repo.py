from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.clients import Client
from app.infrastructure.postgres.repos.clients import PostgresClientRepository


@pytest.mark.asyncio
async def test_add_and_get_by_id(session: AsyncSession, client_repo: PostgresClientRepository):
    c = Client(phone="+998901234567", full_name="Test Client")
    await client_repo.add(c)
    await session.commit()

    found = await client_repo.get_by_id(c.id)
    assert found is not None
    assert found.phone == "+998901234567"
    assert found.full_name == "Test Client"
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_not_found(session: AsyncSession, client_repo: PostgresClientRepository):
    found = await client_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_get_by_phone_found(session: AsyncSession, client_repo: PostgresClientRepository):
    c = Client(phone="+998909999999", full_name="Phone Client")
    await client_repo.add(c)
    await session.commit()

    found = await client_repo.get_by_phone("+998909999999")
    assert found is not None
    assert found.full_name == "Phone Client"


@pytest.mark.asyncio
async def test_get_by_phone_not_found(session: AsyncSession, client_repo: PostgresClientRepository):
    found = await client_repo.get_by_phone("+998900000000")
    assert found is None


@pytest.mark.asyncio
async def test_exists_by_true(session: AsyncSession, client_repo: PostgresClientRepository):
    c = Client(phone="+998901111111", full_name="Exists Client")
    await client_repo.add(c)
    await session.commit()

    assert await client_repo.exists_by(phone="+998901111111") is True


@pytest.mark.asyncio
async def test_exists_by_false(session: AsyncSession, client_repo: PostgresClientRepository):
    assert await client_repo.exists_by(phone="+998900000000") is False


@pytest.mark.asyncio
async def test_list_all_only_active(session: AsyncSession, client_repo: PostgresClientRepository):
    await client_repo.add(Client(phone="+998903000001", full_name="Active"))
    await client_repo.add(Client(phone="+998903000002", full_name="Inactive", is_active=False))
    await session.commit()

    active = await client_repo.list_all(only_active=True)
    assert len(active) == 1
    assert active[0].full_name == "Active"


@pytest.mark.asyncio
async def test_list_all_include_inactive(session: AsyncSession, client_repo: PostgresClientRepository):
    await client_repo.add(Client(phone="+998904000001", full_name="A"))
    await client_repo.add(Client(phone="+998904000002", full_name="B", is_active=False))
    await session.commit()

    all_clients = await client_repo.list_all(only_active=False)
    assert len(all_clients) == 2


@pytest.mark.asyncio
async def test_list_all_empty(session: AsyncSession, client_repo: PostgresClientRepository):
    result = await client_repo.list_all()
    assert result == []


@pytest.mark.asyncio
async def test_update(session: AsyncSession, client_repo: PostgresClientRepository):
    c = Client(phone="+998905000000", full_name="Old Name")
    await client_repo.add(c)
    await session.commit()

    c.full_name = "New Name"
    c.telegram_chat_id = 123456789
    await client_repo.update(c)
    await session.commit()

    found = await client_repo.get_by_id(c.id)
    assert found.full_name == "New Name"
    assert found.telegram_chat_id == 123456789


@pytest.mark.asyncio
async def test_delete(session: AsyncSession, client_repo: PostgresClientRepository):
    c = Client(phone="+998906000000", full_name="ToDelete")
    await client_repo.add(c)
    await session.commit()

    await client_repo.delete(c)
    await session.commit()

    found = await client_repo.get_by_id(c.id)
    assert found is None
