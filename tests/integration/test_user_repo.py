from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.users import User
from app.domain.enums import UserRole
from app.infrastructure.postgres.repos.users import PostgresUserRepository


@pytest.mark.asyncio
async def test_add_and_get_by_id(session: AsyncSession, user_repo: PostgresUserRepository):
    u = User(phone="+998901234567", full_name="Test User")
    await user_repo.add(u)
    await session.commit()

    found = await user_repo.get_by_id(u.id)
    assert found is not None
    assert found.phone == "+998901234567"
    assert found.full_name == "Test User"
    assert found.role == UserRole.CLIENT
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_not_found(session: AsyncSession, user_repo: PostgresUserRepository):
    found = await user_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_get_by_phone_found(session: AsyncSession, user_repo: PostgresUserRepository):
    u = User(phone="+998909999999", full_name="Phone User")
    await user_repo.add(u)
    await session.commit()

    found = await user_repo.get_by_phone("+998909999999")
    assert found is not None
    assert found.full_name == "Phone User"


@pytest.mark.asyncio
async def test_get_by_phone_not_found(session: AsyncSession, user_repo: PostgresUserRepository):
    found = await user_repo.get_by_phone("+998900000000")
    assert found is None


@pytest.mark.asyncio
async def test_exists_by_true(session: AsyncSession, user_repo: PostgresUserRepository):
    u = User(phone="+998901111111", full_name="Exists User")
    await user_repo.add(u)
    await session.commit()

    assert await user_repo.exists_by(phone="+998901111111") is True


@pytest.mark.asyncio
async def test_exists_by_false(session: AsyncSession, user_repo: PostgresUserRepository):
    assert await user_repo.exists_by(phone="+998900000000") is False


@pytest.mark.asyncio
async def test_exists_by_role(session: AsyncSession, user_repo: PostgresUserRepository):
    u = User(phone="+998902222222", full_name="Agent", role=UserRole.AGENT)
    await user_repo.add(u)
    await session.commit()

    assert await user_repo.exists_by(phone="+998902222222", role="agent") is True
    assert await user_repo.exists_by(phone="+998902222222", role="admin") is False


@pytest.mark.asyncio
async def test_list_all_only_active(session: AsyncSession, user_repo: PostgresUserRepository):
    await user_repo.add(User(phone="+998903000001", full_name="Active"))
    await user_repo.add(User(phone="+998903000002", full_name="Inactive", is_active=False))
    await session.commit()

    active = await user_repo.list_all(only_active=True)
    assert len(active) == 1
    assert active[0].full_name == "Active"


@pytest.mark.asyncio
async def test_list_all_include_inactive(session: AsyncSession, user_repo: PostgresUserRepository):
    await user_repo.add(User(phone="+998904000001", full_name="A"))
    await user_repo.add(User(phone="+998904000002", full_name="B", is_active=False))
    await session.commit()

    all_users = await user_repo.list_all(only_active=False)
    assert len(all_users) == 2


@pytest.mark.asyncio
async def test_list_all_empty(session: AsyncSession, user_repo: PostgresUserRepository):
    result = await user_repo.list_all()
    assert result == []


@pytest.mark.asyncio
async def test_update(session: AsyncSession, user_repo: PostgresUserRepository):
    u = User(phone="+998905000000", full_name="Old Name")
    await user_repo.add(u)
    await session.commit()

    u.full_name = "New Name"
    u.role = UserRole.AGENT
    u.telegram_chat_id = 123456789
    await user_repo.update(u)
    await session.commit()

    found = await user_repo.get_by_id(u.id)
    assert found.full_name == "New Name"
    assert found.role == UserRole.AGENT
    assert found.telegram_chat_id == 123456789


@pytest.mark.asyncio
async def test_delete(session: AsyncSession, user_repo: PostgresUserRepository):
    u = User(phone="+998906000000", full_name="ToDelete")
    await user_repo.add(u)
    await session.commit()

    await user_repo.delete(u)
    await session.commit()

    found = await user_repo.get_by_id(u.id)
    assert found is None
