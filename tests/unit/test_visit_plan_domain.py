from datetime import date
from uuid import uuid4

import pytest

from app.domain.entities.visit_plan_items import VisitPlanItem
from app.domain.entities.visit_plans import VisitPlan
from app.domain.enums import VisitPlanItemStatus, VisitPlanStatus, Weekday


def test_visit_plan_creation_defaults():
    emp_id = uuid4()
    today = date(2026, 7, 30)
    plan = VisitPlan(employee_id=emp_id, plan_date=today)

    assert plan.employee_id == emp_id
    assert plan.plan_date == today
    assert plan.status == VisitPlanStatus.PLANNED
    assert plan.items == []
    assert isinstance(plan.id, type(uuid4()))
    assert plan.weekday == Weekday.THURSDAY  # 2026-07-30 is Thursday (weekday 3)


def test_visit_plan_item_validation():
    plan_id = uuid4()
    point_id = uuid4()

    item = VisitPlanItem(visit_plan_id=plan_id, retail_point_id=point_id, order=1)
    assert item.visit_plan_id == plan_id
    assert item.retail_point_id == point_id
    assert item.order == 1
    assert item.status == VisitPlanItemStatus.PENDING

    with pytest.raises(ValueError, match="Order cannot be negative"):
        VisitPlanItem(visit_plan_id=plan_id, retail_point_id=point_id, order=0)


def test_visit_plan_add_item_success():
    emp_id = uuid4()
    plan = VisitPlan(employee_id=emp_id, plan_date=date.today())
    point_id = uuid4()

    item = VisitPlanItem(visit_plan_id=plan.id, retail_point_id=point_id, order=1)
    plan.add_item(item)

    assert len(plan.items) == 1
    assert plan.items[0] == item


def test_visit_plan_add_item_wrong_plan():
    emp_id = uuid4()
    plan = VisitPlan(employee_id=emp_id, plan_date=date.today())
    other_plan_id = uuid4()
    point_id = uuid4()

    item = VisitPlanItem(visit_plan_id=other_plan_id, retail_point_id=point_id, order=1)
    with pytest.raises(ValueError, match="belongs to another visit plan"):
        plan.add_item(item)


def test_visit_plan_add_item_duplicate_order():
    emp_id = uuid4()
    plan = VisitPlan(employee_id=emp_id, plan_date=date.today())

    item1 = VisitPlanItem(visit_plan_id=plan.id, retail_point_id=uuid4(), order=1)
    item2 = VisitPlanItem(visit_plan_id=plan.id, retail_point_id=uuid4(), order=1)

    plan.add_item(item1)
    with pytest.raises(ValueError, match="Duplicate visit plan item order"):
        plan.add_item(item2)
