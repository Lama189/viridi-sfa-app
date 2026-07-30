from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.orders import Order
from app.domain.enums import OrderStatus
from app.infrastructure.postgres.repos.orders import PostgresOrderRepository


@pytest.mark.asyncio
async def test_order_repo_add_get_update_delete(session: AsyncSession):
    repo = PostgresOrderRepository(session)
    wh_id = uuid4()
    client_id = uuid4()
    point_id = uuid4()

    order = Order(
        warehouse_id=wh_id,
        created_by_id=client_id,
        retail_point_id=point_id,
    )

    await repo.add(order)
    await session.commit()

    found = await repo.get_by_id(order.id)
    assert found is not None
    assert found.warehouse_id == wh_id
    assert found.created_by_id == client_id

    by_client = await repo.list_by_client(client_id)
    assert len(by_client) == 1

    by_point = await repo.list_by_retail_point(point_id)
    assert len(by_point) == 1

    order.status = OrderStatus.CONFIRMED
    await repo.update(order)
    await session.commit()

    updated = await repo.get_by_id(order.id)
    assert updated.status == OrderStatus.CONFIRMED

    await repo.delete(order)
    await session.commit()

    deleted = await repo.get_by_id(order.id)
    assert deleted is None
