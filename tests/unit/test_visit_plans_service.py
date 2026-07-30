from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.visit_plans import VisitPlanService
from app.core.extensions import VisitPlanAlreadyExistsError, VisitPlanNotFoundError
from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.visit_plans import VisitPlan


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.visit_plans = AsyncMock()
    uow.visit_plan_items = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return VisitPlanService(uow=mock_uow)


@pytest.mark.asyncio
async def test_create_plan_success(service, mock_uow):
    plan = VisitPlan(employee_id=uuid4(), plan_date=date.today())

    result = await service.create_plan(plan)

    assert result == plan
    mock_uow.visit_plans.add.assert_awaited_once_with(plan)


@pytest.mark.asyncio
async def test_generate_for_employee_new_plan(service, mock_uow):
    emp_id = uuid4()
    plan_date = date(2026, 8, 3)
    p1 = RetailPoint(name="P1", address="Addr B")
    p2 = RetailPoint(name="P2", address="Addr A")

    mock_uow.visit_plans.get_by_employee_and_date.return_value = None
    mock_uow.retail_points.list_by_employee_and_weekday.return_value = [p1, p2]

    plan = await service.generate_for_employee(emp_id, plan_date)

    assert plan.employee_id == emp_id
    assert plan.plan_date == plan_date
    assert len(plan.items) == 2
    # Sorted by address: Addr A first, then Addr B
    assert plan.items[0].retail_point_id == p2.id
    assert plan.items[0].order == 1
    assert plan.items[1].retail_point_id == p1.id
    assert plan.items[1].order == 2


@pytest.mark.asyncio
async def test_generate_for_employee_existing_plan_overwrite(service, mock_uow):
    emp_id = uuid4()
    plan_date = date(2026, 8, 3)
    existing_plan = VisitPlan(employee_id=emp_id, plan_date=plan_date)
    p1 = RetailPoint(name="P1", address="Addr A")

    mock_uow.visit_plans.get_by_employee_and_date.return_value = existing_plan
    mock_uow.retail_points.list_by_employee_and_weekday.return_value = [p1]

    plan = await service.generate_for_employee(emp_id, plan_date, overwrite=True)

    mock_uow.visit_plan_items.delete_by_plan.assert_awaited_once_with(existing_plan.id)
    assert plan.id == existing_plan.id
    assert len(plan.items) == 1


@pytest.mark.asyncio
async def test_generate_for_employee_existing_plan_no_overwrite(service, mock_uow):
    emp_id = uuid4()
    plan_date = date(2026, 8, 3)
    existing_plan = VisitPlan(employee_id=emp_id, plan_date=plan_date)

    mock_uow.visit_plans.get_by_employee_and_date.return_value = existing_plan

    with pytest.raises(VisitPlanAlreadyExistsError):
        await service.generate_for_employee(emp_id, plan_date, overwrite=False)


@pytest.mark.asyncio
async def test_get_by_employee_and_date_found(service, mock_uow):
    emp_id = uuid4()
    plan_date = date.today()
    plan = VisitPlan(employee_id=emp_id, plan_date=plan_date)

    mock_uow.visit_plans.get_by_employee_and_date.return_value = plan
    mock_uow.visit_plan_items.list_by_plan.return_value = []

    result = await service.get_by_employee_and_date(emp_id, plan_date)

    assert result == plan


@pytest.mark.asyncio
async def test_get_by_employee_and_date_not_found(service, mock_uow):
    mock_uow.visit_plans.get_by_employee_and_date.return_value = None

    with pytest.raises(VisitPlanNotFoundError):
        await service.get_by_employee_and_date(uuid4(), date.today())


@pytest.mark.asyncio
async def test_get_today_plan(service, mock_uow):
    emp_id = uuid4()
    today = date.today()
    plan = VisitPlan(employee_id=emp_id, plan_date=today)

    mock_uow.visit_plans.get_by_employee_and_date.return_value = plan
    mock_uow.visit_plan_items.list_by_plan.return_value = []

    result = await service.get_today_plan(emp_id)

    assert result == plan
