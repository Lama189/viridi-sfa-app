from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.dashboard import DashboardService
from app.core.extensions import VisitPlanNotFoundError
from app.domain.entities.visit_plans import VisitPlan


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.visit_plans = AsyncMock()
    uow.visit_plan_items = AsyncMock()
    uow.visits = AsyncMock()
    uow.orders = AsyncMock()
    uow.visit_debts = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return DashboardService(uow=mock_uow)


@pytest.mark.asyncio
async def test_get_employee_dashboard_no_plan(service, mock_uow):
    emp_id = uuid4()
    mock_uow.visit_plans.get_by_employee_and_date.return_value = None

    with pytest.raises(VisitPlanNotFoundError):
        await service.get_employee_dashboard(emp_id)

    mock_uow.visit_plans.get_by_employee_and_date.assert_awaited_once_with(
        emp_id,
        date.today(),
    )


@pytest.mark.asyncio
async def test_get_employee_dashboard_zero_total_points(service, mock_uow):
    emp_id = uuid4()
    today = date.today()
    plan = VisitPlan(employee_id=emp_id, plan_date=today)

    mock_uow.visit_plans.get_by_employee_and_date.return_value = plan
    mock_uow.visit_plan_items.count_by_plan_id.return_value = 0
    mock_uow.visits.count_completed_by_plan.return_value = 0
    mock_uow.orders.get_statistics_by_employee_and_date.return_value = (0, Decimal("0.00"))
    mock_uow.visit_debts.count_by_employee_and_date.return_value = 0

    dashboard = await service.get_employee_dashboard(emp_id)

    assert dashboard.total_points == 0
    assert dashboard.completed_points == 0
    assert dashboard.remaining_points == 0
    assert dashboard.completion_percentage == Decimal("0")
    assert dashboard.orders_count == 0
    assert dashboard.orders_amount == Decimal("0.00")
    assert dashboard.debts_count == 0


@pytest.mark.asyncio
async def test_get_employee_dashboard_success(service, mock_uow):
    emp_id = uuid4()
    today = date.today()
    plan = VisitPlan(employee_id=emp_id, plan_date=today)

    mock_uow.visit_plans.get_by_employee_and_date.return_value = plan
    mock_uow.visit_plan_items.count_by_plan_id.return_value = 25
    mock_uow.visits.count_completed_by_plan.return_value = 12
    mock_uow.orders.get_statistics_by_employee_and_date.return_value = (8, Decimal("1250000.00"))
    mock_uow.visit_debts.count_by_employee_and_date.return_value = 3

    dashboard = await service.get_employee_dashboard(emp_id)

    assert dashboard.total_points == 25
    assert dashboard.completed_points == 12
    assert dashboard.remaining_points == 13
    assert dashboard.completion_percentage == Decimal("48")
    assert dashboard.orders_count == 8
    assert dashboard.orders_amount == Decimal("1250000.00")
    assert dashboard.debts_count == 3
