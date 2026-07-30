from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.stocks import Stock
from app.infrastructure.postgres.repos.stocks import PostgresStocksRepository


@pytest.mark.asyncio
async def test_stock_repo_operations(session: AsyncSession):
    repo = PostgresStocksRepository(session)
    wh_id = uuid4()
    prod_id = uuid4()

    stock = Stock(warehouse_id=wh_id, product_id=prod_id, quantity=100, reserved_quantity=10)
    await repo.add(stock)
    await session.commit()

    found = await repo.get(wh_id, prod_id)
    assert found is not None
    assert found.quantity == 100
    assert found.reserved_quantity == 10

    by_wh = await repo.list_by_warehouse(wh_id)
    assert len(by_wh) == 1

    assert await repo.exists_by(warehouse_id=wh_id) is True

    stock.quantity = 90
    await repo.update(stock)
    await session.commit()

    updated = await repo.get(wh_id, prod_id)
    assert updated.quantity == 90

    await repo.delete(stock)
    await session.commit()

    deleted = await repo.get(wh_id, prod_id)
    assert deleted is None
