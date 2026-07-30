from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.retail_points import RetailPoint
from app.infrastructure.postgres.repos.retail_points import PostgresRetailPointRepository


@pytest.mark.asyncio
async def test_add_and_get_by_id(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    rp = RetailPoint(name="Store-1", address="ul. Test 1")
    await retail_point_repo.add(rp)
    await session.commit()

    found = await retail_point_repo.get_by_id(rp.id)
    assert found is not None
    assert found.name == "Store-1"
    assert found.address == "ul. Test 1"
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    found = await retail_point_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_exists_by_true(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    rp = RetailPoint(name="Exists-1", address="addr")
    await retail_point_repo.add(rp)
    await session.commit()

    assert await retail_point_repo.exists_by(name="Exists-1") is True


@pytest.mark.asyncio
async def test_exists_by_false(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    assert await retail_point_repo.exists_by(name="Nonexistent") is False


@pytest.mark.asyncio
async def test_list_all_only_active(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    await retail_point_repo.add(RetailPoint(name="Active", address="a"))
    await retail_point_repo.add(RetailPoint(name="Inactive", address="b", is_active=False))
    await session.commit()

    active = await retail_point_repo.list_all(only_active=True)
    assert len(active) == 1
    assert active[0].name == "Active"


@pytest.mark.asyncio
async def test_list_all_include_inactive(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    await retail_point_repo.add(RetailPoint(name="A", address="a"))
    await retail_point_repo.add(RetailPoint(name="B", address="b", is_active=False))
    await session.commit()

    all_rp = await retail_point_repo.list_all(only_active=False)
    assert len(all_rp) == 2


@pytest.mark.asyncio
async def test_list_all_empty(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    result = await retail_point_repo.list_all()
    assert result == []


@pytest.mark.asyncio
async def test_update(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    rp = RetailPoint(name="Old", address="Old Addr")
    await retail_point_repo.add(rp)
    await session.commit()

    rp.name = "New"
    rp.address = "New Addr"
    rp.latitude = Decimal("41.311081")
    await retail_point_repo.update(rp)
    await session.commit()

    found = await retail_point_repo.get_by_id(rp.id)
    assert found.name == "New"
    assert found.address == "New Addr"
    assert found.latitude == Decimal("41.311081")


@pytest.mark.asyncio
async def test_delete(
    session: AsyncSession,
    retail_point_repo: PostgresRetailPointRepository,
):
    rp = RetailPoint(name="ToDelete", address="D")
    await retail_point_repo.add(rp)
    await session.commit()

    await retail_point_repo.delete(rp)
    await session.commit()

    found = await retail_point_repo.get_by_id(rp.id)
    assert found is None
