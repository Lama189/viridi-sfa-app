from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.visit_plans import VisitPlan
from app.infrastructure.postgres.repos.visit_plans import PostgresVisitPlanRepository


@pytest.mark.asyncio
async def test_visit_plan_repo_add_get(session: AsyncSession):
    repo = PostgresVisitPlanRepository(session)
    emp_id = uuid4()
    plan_date = date(2026, 8, 3)

    plan = VisitPlan(employee_id=emp_id, plan_date=plan_date)
    await repo.add(plan)
    await session.commit()

    found = await repo.get_by_id(plan.id)
    assert found is not None
    assert found.id == plan.id
    assert found.employee_id == emp_id
    assert found.plan_date == plan_date

    found_by_emp = await repo.get_by_employee_and_date(emp_id, plan_date)
    assert found_by_emp is not None
    assert found_by_emp.id == plan.id

    list_emp = await repo.list_by_employee(emp_id)
    assert len(list_emp) == 1
    assert list_emp[0].id == plan.id


@pytest.mark.asyncio
async def test_visit_plan_repo_delete_all(session: AsyncSession):
    repo = PostgresVisitPlanRepository(session)
    plan1 = VisitPlan(employee_id=uuid4(), plan_date=date(2026, 8, 3))
    plan2 = VisitPlan(employee_id=uuid4(), plan_date=date(2026, 8, 4))
    await repo.add(plan1)
    await repo.add(plan2)
    await session.commit()

    await repo.delete_all()
    await session.commit()

    found1 = await repo.get_by_id(plan1.id)
    found2 = await repo.get_by_id(plan2.id)
    assert found1 is None
    assert found2 is None
