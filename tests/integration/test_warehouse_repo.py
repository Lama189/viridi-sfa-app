import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.inventory import Warehouse
from app.infrastructure.postgres.repos.warehouses import PostgresWarehousesRepository


@pytest.mark.asyncio
async def test_add_and_get_by_id(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    w = Warehouse(name="Warehouse-1", address="ul. Test 1")
    await warehouse_repo.add(w)
    await session.commit()

    found = await warehouse_repo.get_by_id(w.id)
    assert found is not None
    assert found.name == "Warehouse-1"
    assert found.address == "ul. Test 1"
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    from uuid import uuid4

    found = await warehouse_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_exists_by_true(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    w = Warehouse(name="Exists-1")
    await warehouse_repo.add(w)
    await session.commit()

    assert await warehouse_repo.exists_by(name="Exists-1") is True


@pytest.mark.asyncio
async def test_exists_by_false(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    assert await warehouse_repo.exists_by(name="Nonexistent") is False


@pytest.mark.asyncio
async def test_exists_by_is_active(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    w = Warehouse(name="Active-1", is_active=True)
    await warehouse_repo.add(w)
    await session.commit()

    assert await warehouse_repo.exists_by(name="Active-1", is_active=True) is True
    assert await warehouse_repo.exists_by(name="Active-1", is_active=False) is False


@pytest.mark.asyncio
async def test_list_all_only_active(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    await warehouse_repo.add(Warehouse(name="Active"))
    await warehouse_repo.add(Warehouse(name="Inactive", is_active=False))
    await session.commit()

    active = await warehouse_repo.list_all(only_active=True)
    assert len(active) == 1
    assert active[0].name == "Active"


@pytest.mark.asyncio
async def test_list_all_include_inactive(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    await warehouse_repo.add(Warehouse(name="A"))
    await warehouse_repo.add(Warehouse(name="B", is_active=False))
    await session.commit()

    all_wh = await warehouse_repo.list_all(only_active=False)
    assert len(all_wh) == 2


@pytest.mark.asyncio
async def test_list_all_empty(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    result = await warehouse_repo.list_all()
    assert result == []


@pytest.mark.asyncio
async def test_update(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    w = Warehouse(name="Old", address="Old Addr")
    await warehouse_repo.add(w)
    await session.commit()

    w.name = "New"
    w.address = "New Addr"
    await warehouse_repo.update(w)
    await session.commit()

    found = await warehouse_repo.get_by_id(w.id)
    assert found.name == "New"
    assert found.address == "New Addr"


@pytest.mark.asyncio
async def test_delete(
    session: AsyncSession, warehouse_repo: PostgresWarehousesRepository
):
    w = Warehouse(name="ToDelete")
    await warehouse_repo.add(w)
    await session.commit()

    await warehouse_repo.delete(w)
    await session.commit()

    found = await warehouse_repo.get_by_id(w.id)
    assert found is None
