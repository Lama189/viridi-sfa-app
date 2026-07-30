from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.orders import OrderItem
from app.infrastructure.postgres.repos.order_items import PostgresOrderItemRepository


@pytest.mark.asyncio
async def test_order_item_repo_add_list_delete(session: AsyncSession):
    repo = PostgresOrderItemRepository(session)
    order_id = uuid4()
    prod_id = uuid4()

    item = OrderItem(
        order_id=order_id,
        product_id=prod_id,
        quantity=5,
        price_at_order=Decimal("100.00"),
        total_volume=Decimal("5.0"),
    )

    await repo.add(item)
    await session.commit()

    items = await repo.list_by_order(order_id)
    assert len(items) == 1
    assert items[0].product_id == prod_id
    assert items[0].quantity == 5

    await repo.delete_by_order(order_id)
    await session.commit()

    items_after = await repo.list_by_order(order_id)
    assert len(items_after) == 0
