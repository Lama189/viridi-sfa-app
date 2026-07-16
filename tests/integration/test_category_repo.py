import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.inventory import Category
from app.infrastructure.postgres.repos.categories import PostgresCategoriesRepository


@pytest.mark.asyncio
async def test_add_and_get_by_id(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    c = Category(name="Fertilizers")
    await category_repo.add(c)
    await session.commit()

    found = await category_repo.get_by_id(c.id)
    assert found is not None
    assert found.name == "Fertilizers"
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_not_found(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    found = await category_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_exists_by_true(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    c = Category(name="Seeds")
    await category_repo.add(c)
    await session.commit()

    assert await category_repo.exists_by(name="Seeds") is True


@pytest.mark.asyncio
async def test_exists_by_false(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    assert await category_repo.exists_by(name="Nonexistent") is False


@pytest.mark.asyncio
async def test_exists_by_is_active(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    c = Category(name="Tools", is_active=True)
    await category_repo.add(c)
    await session.commit()

    assert await category_repo.exists_by(name="Tools", is_active=True) is True
    assert await category_repo.exists_by(name="Tools", is_active=False) is False


@pytest.mark.asyncio
async def test_list_all_only_active(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    await category_repo.add(Category(name="Active"))
    await category_repo.add(Category(name="Inactive", is_active=False))
    await session.commit()

    active = await category_repo.list_all(only_active=True)
    assert len(active) == 1
    assert active[0].name == "Active"


@pytest.mark.asyncio
async def test_list_all_include_inactive(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    await category_repo.add(Category(name="A"))
    await category_repo.add(Category(name="B", is_active=False))
    await session.commit()

    all_cat = await category_repo.list_all(only_active=False)
    assert len(all_cat) == 2


@pytest.mark.asyncio
async def test_list_all_empty(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    result = await category_repo.list_all()
    assert result == []


@pytest.mark.asyncio
async def test_update(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    c = Category(name="Old")
    await category_repo.add(c)
    await session.commit()

    c.name = "New"
    await category_repo.update(c)
    await session.commit()

    found = await category_repo.get_by_id(c.id)
    assert found.name == "New"


@pytest.mark.asyncio
async def test_delete(session: AsyncSession, category_repo: PostgresCategoriesRepository):
    c = Category(name="ToDelete")
    await category_repo.add(c)
    await session.commit()

    await category_repo.delete(c)
    await session.commit()

    found = await category_repo.get_by_id(c.id)
    assert found is None
