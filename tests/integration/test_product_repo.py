import pytest
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.inventory import Category, Product
from app.infrastructure.postgres.repos.categories import PostgresCategoriesRepository
from app.infrastructure.postgres.repos.products import PostgresProductsRepository


@pytest.mark.asyncio
async def test_add_and_get_by_id(
    session: AsyncSession,
    category_repo: PostgresCategoriesRepository,
    product_repo: PostgresProductsRepository,
):
    c = Category(name="Fertilizers")
    await category_repo.add(c)
    await session.flush()

    p = Product(category_id=c.id, name="NPK-10", price=Decimal("150.00"))
    await product_repo.add(p)
    await session.commit()

    found = await product_repo.get_by_id(p.id)
    assert found is not None
    assert found.name == "NPK-10"
    assert found.category_id == c.id
    assert found.price == Decimal("150.00")
    assert found.volume == Decimal("0.000")
    assert found.weight == Decimal("0.000")
    assert found.items_in_box == 1
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_not_found(session: AsyncSession, product_repo: PostgresProductsRepository):
    found = await product_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_exists_by_true(
    session: AsyncSession,
    category_repo: PostgresCategoriesRepository,
    product_repo: PostgresProductsRepository,
):
    c = Category(name="Seeds")
    await category_repo.add(c)
    await session.flush()

    p = Product(category_id=c.id, name="Tomato", price=Decimal("50.00"))
    await product_repo.add(p)
    await session.commit()

    assert await product_repo.exists_by(name="Tomato") is True


@pytest.mark.asyncio
async def test_exists_by_false(session: AsyncSession, product_repo: PostgresProductsRepository):
    assert await product_repo.exists_by(name="Nonexistent") is False


@pytest.mark.asyncio
async def test_exists_by_price(
    session: AsyncSession,
    category_repo: PostgresCategoriesRepository,
    product_repo: PostgresProductsRepository,
):
    c = Category(name="Tools")
    await category_repo.add(c)
    await session.flush()

    p = Product(category_id=c.id, name="Shovel", price=Decimal("200.00"))
    await product_repo.add(p)
    await session.commit()

    assert await product_repo.exists_by(name="Shovel", price=Decimal("200.00")) is True
    assert await product_repo.exists_by(name="Shovel", price=Decimal("999.00")) is False


@pytest.mark.asyncio
async def test_list_all_only_active(
    session: AsyncSession,
    category_repo: PostgresCategoriesRepository,
    product_repo: PostgresProductsRepository,
):
    c = Category(name="Cat")
    await category_repo.add(c)
    await session.flush()

    await product_repo.add(Product(category_id=c.id, name="Active", price=Decimal("10.00")))
    await product_repo.add(Product(category_id=c.id, name="Inactive", price=Decimal("20.00"), is_active=False))
    await session.commit()

    active = await product_repo.list_all(only_active=True)
    assert len(active) == 1
    assert active[0].name == "Active"


@pytest.mark.asyncio
async def test_list_all_include_inactive(
    session: AsyncSession,
    category_repo: PostgresCategoriesRepository,
    product_repo: PostgresProductsRepository,
):
    c = Category(name="Cat")
    await category_repo.add(c)
    await session.flush()

    await product_repo.add(Product(category_id=c.id, name="A", price=Decimal("10.00")))
    await product_repo.add(Product(category_id=c.id, name="B", price=Decimal("20.00"), is_active=False))
    await session.commit()

    all_p = await product_repo.list_all(only_active=False)
    assert len(all_p) == 2


@pytest.mark.asyncio
async def test_list_all_empty(session: AsyncSession, product_repo: PostgresProductsRepository):
    result = await product_repo.list_all()
    assert result == []


@pytest.mark.asyncio
async def test_update(
    session: AsyncSession,
    category_repo: PostgresCategoriesRepository,
    product_repo: PostgresProductsRepository,
):
    c = Category(name="Cat")
    await category_repo.add(c)
    await session.flush()

    p = Product(category_id=c.id, name="Old", price=Decimal("10.00"), volume=Decimal("1.000"), weight=Decimal("0.500"), items_in_box=10)
    await product_repo.add(p)
    await session.commit()

    p.name = "New"
    p.price = Decimal("99.99")
    p.volume = Decimal("2.500")
    p.weight = Decimal("1.200")
    p.items_in_box = 25
    await product_repo.update(p)
    await session.commit()

    found = await product_repo.get_by_id(p.id)
    assert found.name == "New"
    assert found.price == Decimal("99.99")
    assert found.volume == Decimal("2.500")
    assert found.weight == Decimal("1.200")
    assert found.items_in_box == 25


@pytest.mark.asyncio
async def test_delete(
    session: AsyncSession,
    category_repo: PostgresCategoriesRepository,
    product_repo: PostgresProductsRepository,
):
    c = Category(name="Cat")
    await category_repo.add(c)
    await session.flush()

    p = Product(category_id=c.id, name="ToDelete", price=Decimal("10.00"))
    await product_repo.add(p)
    await session.commit()

    await product_repo.delete(p)
    await session.commit()

    found = await product_repo.get_by_id(p.id)
    assert found is None
