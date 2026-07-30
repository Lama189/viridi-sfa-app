from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.visit_plan_items import VisitPlanItem
from app.infrastructure.postgres.repos.visit_plan_items import PostgresVisitPlanItemRepository


@pytest.mark.asyncio
async def test_visit_plan_item_repo_operations(session: AsyncSession):
    repo = PostgresVisitPlanItemRepository(session)
    plan_id = uuid4()
    point1 = uuid4()
    point2 = uuid4()

    item1 = VisitPlanItem(visit_plan_id=plan_id, retail_point_id=point1, order=1)
    item2 = VisitPlanItem(visit_plan_id=plan_id, retail_point_id=point2, order=2)

    await repo.add_many([item1, item2])
    await session.commit()

    items = await repo.list_by_plan(plan_id)
    assert len(items) == 2
    assert items[0].order == 1
    assert items[1].order == 2

    await repo.delete_by_plan(plan_id)
    await session.commit()

    items_after = await repo.list_by_plan(plan_id)
    assert items_after == []
