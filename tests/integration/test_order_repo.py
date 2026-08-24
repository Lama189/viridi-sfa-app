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

    source_vid = uuid4()
    actual_vid = uuid4()
    order.source_visit_id = source_vid
    order.actual_visit_id = actual_vid
    order.status = OrderStatus.CONFIRMED
    await repo.update(order)
    await session.commit()

    updated = await repo.get_by_id(order.id)
    assert updated.status == OrderStatus.CONFIRMED
    assert updated.source_visit_id == source_vid
    assert updated.actual_visit_id == actual_vid

    by_source = await repo.list_by_source_visit(source_vid)
    assert len(by_source) == 1
    assert by_source[0].id == order.id

    by_actual = await repo.list_by_actual_visit(actual_vid)
    assert len(by_actual) == 1
    assert by_actual[0].id == order.id

    await repo.delete(order)
    await session.commit()

    deleted = await repo.get_by_id(order.id)
    assert deleted is None
