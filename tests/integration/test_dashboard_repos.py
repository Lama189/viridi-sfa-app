from datetime import date, datetime, UTC
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.visit_plans import VisitPlan
from app.domain.entities.visit_plan_items import VisitPlanItem
from app.domain.entities.visits import Visit
from app.domain.entities.orders import Order
from app.domain.entities.visit_debts import VisitDebt
from app.domain.enums import VisitStatus
from app.infrastructure.postgres.repos.visit_plans import PostgresVisitPlanRepository
from app.infrastructure.postgres.repos.visit_plan_items import PostgresVisitPlanItemRepository
from app.infrastructure.postgres.repos.visits import PostgresVisitRepository
from app.infrastructure.postgres.repos.orders import PostgresOrderRepository
from app.infrastructure.postgres.repos.visit_debts import PostgresVisitDebtRepository


@pytest.mark.asyncio
async def test_dashboard_repos_aggregations(session: AsyncSession):
    emp_id = uuid4()
    rp_id1 = uuid4()
    rp_id2 = uuid4()
    client_id = uuid4()
    warehouse_id = uuid4()
    today = date.today()

    plan_repo = PostgresVisitPlanRepository(session)
    item_repo = PostgresVisitPlanItemRepository(session)
    visit_repo = PostgresVisitRepository(session)
    order_repo = PostgresOrderRepository(session)
    debt_repo = PostgresVisitDebtRepository(session)

    # 1. Create visit plan & items
    plan = VisitPlan(employee_id=emp_id, plan_date=today)
    await plan_repo.add(plan)
    
    item1 = VisitPlanItem(visit_plan_id=plan.id, retail_point_id=rp_id1, order=1)
    item2 = VisitPlanItem(visit_plan_id=plan.id, retail_point_id=rp_id2, order=2)
    await item_repo.add_many([item1, item2])
    await session.commit()

    count_items = await item_repo.count_by_plan_id(plan.id)
    assert count_items == 2

    # 2. Create completed visit for rp_id1
    visit1 = Visit(
        employee_id=emp_id,
        retail_point_id=rp_id1,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        status=VisitStatus.COMPLETED,
    )
    await visit_repo.add(visit1)
    await session.commit()

    completed_count = await visit_repo.count_completed_by_plan(plan.id, emp_id)
    assert completed_count == 1

    # 3. Create order for visit1
    order1 = Order(
        warehouse_id=warehouse_id,
        created_by_id=client_id,
        retail_point_id=rp_id1,
        visit_id=visit1.id,
        total_amount=Decimal("50000.00"),
    )
    await order_repo.add(order1)
    await session.commit()

    orders_count, orders_amount = await order_repo.get_statistics_by_employee_and_date(emp_id, today)
    assert orders_count == 1
    assert orders_amount == Decimal("50000.00")

    # 4. Create debt for visit1
    debt1 = VisitDebt(
        visit_id=visit1.id,
        amount=15000.0,
        comment="Test debt",
    )
    await debt_repo.add(debt1)
    await session.commit()

    debts_count = await debt_repo.count_by_employee_and_date(emp_id, today)
    assert debts_count == 1
