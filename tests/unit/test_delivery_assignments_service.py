from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from firebase_admin.exceptions import FirebaseError

from app.application.services.delivery_assignments import DeliveryAssignmentService
from app.domain.entities.orders import Order
from app.domain.entities.retail_point_assignments import RetailPointAssignment
from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.visit_plans import VisitPlan
from app.domain.enums import OrderStatus, VisitPlanStatus


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.orders = AsyncMock()
    uow.retail_point_assignments = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.visit_plans = AsyncMock()
    uow.outbox = AsyncMock()
    uow.notifications = AsyncMock()
    return uow


@pytest.fixture
def mock_push_service():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_push_service):
    return DeliveryAssignmentService(
        uow=mock_uow,
        push_service=mock_push_service,
    )


@pytest.mark.asyncio
async def test_assign_order_to_next_visit_success(service, mock_uow, mock_push_service):
    order_id = uuid4()
    retail_point_id = uuid4()
    employee_id = uuid4()
    plan_id = uuid4()
    plan_date = date.today() + timedelta(days=1)

    order = Order(
        id=order_id,
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=retail_point_id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("250000.00"),
        total_volume=Decimal("0.500"),
    )

    assignment = RetailPointAssignment(
        retail_point_id=retail_point_id,
        employee_id=employee_id,
    )
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment

    rp = RetailPoint(
        id=retail_point_id,
        name="Супермаркет Корзинка",
        address="ул. Навои, 1",
        latitude=Decimal("41.311"),
        longitude=Decimal("69.279"),
        created_by_employee_id=employee_id,
    )
    mock_uow.retail_points.get_by_id.return_value = rp

    visit_plan = VisitPlan(
        id=plan_id,
        employee_id=employee_id,
        plan_date=plan_date,
        status=VisitPlanStatus.PLANNED,
    )
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = visit_plan

    result = await service.assign_order_to_next_visit(order)

    assert result == visit_plan
    assert order.planned_visit_id == plan_id

    # Check outbox PLANNED event was added
    mock_uow.outbox.add.assert_awaited_once()
    outbox_call = mock_uow.outbox.add.call_args[0][0]
    assert outbox_call.event_type == "order.planned"
    assert outbox_call.payload["order_id"] == str(order_id)
    assert outbox_call.payload["planned_visit_id"] == str(plan_id)

    # Check notification was added without commit
    mock_uow.notifications.add.assert_awaited_once()
    notif_call = mock_uow.notifications.add.call_args[0][0]
    assert notif_call.employee_id == employee_id
    assert notif_call.title == "Заказ назначен на ваш визит"
    assert notif_call.notification_type == "order_assigned_to_visit"
    assert "Корзинка" in notif_call.body
    assert notif_call.payload["planned_visit_id"] == str(plan_id)

    # Check push was sent
    mock_push_service.send_to_employee.assert_awaited_once_with(
        employee_id=employee_id,
        title="Заказ назначен на ваш визит",
        body=f"Точка «Супермаркет Корзинка», {plan_date.strftime('%d.%m.%Y')}",
        data={
            "order_id": str(order_id),
            "retail_point_id": str(retail_point_id),
            "retail_point_name": "Супермаркет Корзинка",
            "planned_visit_id": str(plan_id),
            "plan_date": str(plan_date),
            "total_amount": "250000.00",
            "total_volume": "0.500",
            "notification_type": "order_assigned_to_visit",
        },
    )

    # Critical: DeliveryAssignmentService MUST NOT call commit
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_order_invalid_status(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.LOADED,
    )
    result = await service.assign_order_to_next_visit(order)
    assert result is None
    mock_uow.outbox.add.assert_not_awaited()
    mock_uow.notifications.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_order_no_assignment(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.CONFIRMED,
    )
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = None

    result = await service.assign_order_to_next_visit(order)
    assert result is None
    assert order.planned_visit_id is None
    mock_uow.outbox.add.assert_not_awaited()
    mock_uow.notifications.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_order_no_visit_plan(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.CONFIRMED,
    )
    assignment = RetailPointAssignment(
        retail_point_id=order.retail_point_id,
        employee_id=uuid4(),
    )
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = None

    result = await service.assign_order_to_next_visit(order)
    assert result is None
    assert order.planned_visit_id is None
    mock_uow.outbox.add.assert_not_awaited()
    mock_uow.notifications.add.assert_not_awaited()


@pytest.mark.asyncio
async def test_assign_order_push_error_does_not_fail_assignment(
    service, mock_uow, mock_push_service
):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.CONFIRMED,
    )
    assignment = RetailPointAssignment(
        retail_point_id=order.retail_point_id,
        employee_id=uuid4(),
    )
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment

    visit_plan = VisitPlan(
        id=uuid4(),
        employee_id=assignment.employee_id,
        plan_date=date.today(),
        status=VisitPlanStatus.PLANNED,
    )
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = visit_plan
    mock_uow.retail_points.get_by_id.return_value = None
    mock_push_service.send_to_employee.side_effect = FirebaseError("500", "FCM failure")

    result = await service.assign_order_to_next_visit(order)
    assert result == visit_plan
    assert order.planned_visit_id == visit_plan.id
    mock_uow.outbox.add.assert_awaited_once()
    mock_uow.notifications.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_order_by_id_success(service, mock_uow):
    order_id = uuid4()
    order = Order(
        id=order_id,
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.CONFIRMED,
    )
    mock_uow.orders.get_by_id.return_value = order

    assignment = RetailPointAssignment(
        retail_point_id=order.retail_point_id,
        employee_id=uuid4(),
    )
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment

    visit_plan = VisitPlan(
        id=uuid4(),
        employee_id=assignment.employee_id,
        plan_date=date.today(),
        status=VisitPlanStatus.PLANNED,
    )
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = visit_plan
    mock_uow.retail_points.get_by_id.return_value = None

    result = await service.assign_order_by_id(order_id)
    assert result == visit_plan
    assert order.planned_visit_id == visit_plan.id
    mock_uow.orders.update.assert_awaited_once_with(order)


@pytest.mark.asyncio
async def test_assign_order_by_id_not_found(service, mock_uow):
    mock_uow.orders.get_by_id.return_value = None
    result = await service.assign_order_by_id(uuid4())
    assert result is None
