from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.delivery_proposals import DeliveryProposalService
from app.domain.entities.notifications import Notification
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
    return uow


@pytest.fixture
def mock_notifications_service():
    return AsyncMock()


@pytest.fixture
def mock_push_service():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_notifications_service, mock_push_service):
    return DeliveryProposalService(
        uow=mock_uow,
        notifications_service=mock_notifications_service,
        push_service=mock_push_service,
    )


@pytest.mark.asyncio
async def test_notify_order_assigned_success(
    service, mock_uow, mock_notifications_service, mock_push_service
):
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
        planned_visit_id=plan_id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("250000.00"),
        total_volume=Decimal("0.500"),
    )
    mock_uow.orders.get_by_id.return_value = order

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
    mock_uow.visit_plans.get_by_id.return_value = visit_plan

    expected_notification = Notification(
        id=uuid4(),
        employee_id=employee_id,
        title="Заказ назначен на ваш визит",
        body="Тест",
        notification_type="order_assigned_to_visit",
    )
    mock_notifications_service.create.return_value = expected_notification

    result = await service.notify_order_assigned(order_id)

    assert result == expected_notification
    mock_notifications_service.create.assert_awaited_once()
    dto = mock_notifications_service.create.call_args[0][0]
    assert dto.employee_id == employee_id
    assert dto.title == "Заказ назначен на ваш визит"
    assert dto.notification_type == "order_assigned_to_visit"
    assert "Корзинка" in dto.body
    assert dto.payload["order_id"] == str(order_id)
    assert dto.payload["retail_point_id"] == str(retail_point_id)
    assert dto.payload["retail_point_name"] == "Супермаркет Корзинка"
    assert dto.payload["planned_visit_id"] == str(plan_id)

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


@pytest.mark.asyncio
async def test_notify_order_assigned_not_found(service, mock_uow):
    mock_uow.orders.get_by_id.return_value = None
    result = await service.notify_order_assigned(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_notify_order_assigned_no_assignment(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.CONFIRMED,
    )
    mock_uow.orders.get_by_id.return_value = order
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = None

    result = await service.notify_order_assigned(order.id)
    assert result is None


@pytest.mark.asyncio
async def test_notify_order_assigned_no_visit_plan(service, mock_uow):
    order = Order(
        id=uuid4(),
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
    mock_uow.visit_plans.get_by_id.return_value = None
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = None

    result = await service.notify_order_assigned(order.id)
    assert result is None


@pytest.mark.asyncio
async def test_plan_order_delivery_success(
    service, mock_uow, mock_notifications_service, mock_push_service
):
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
    mock_uow.orders.get_by_id.return_value = order

    assignment = RetailPointAssignment(
        retail_point_id=retail_point_id,
        employee_id=employee_id,
    )
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment

    visit_plan = VisitPlan(
        id=plan_id,
        employee_id=employee_id,
        plan_date=plan_date,
        status=VisitPlanStatus.PLANNED,
    )
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = visit_plan
    mock_uow.visit_plans.get_by_id.return_value = visit_plan

    result = await service.plan_order_delivery(order_id)

    assert result == order
    assert order.planned_visit_id == plan_id
    mock_uow.orders.update.assert_awaited_once_with(order)
    mock_uow.outbox.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()
    mock_notifications_service.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_plan_order_delivery_not_found(service, mock_uow):
    mock_uow.orders.get_by_id.return_value = None
    result = await service.plan_order_delivery(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_plan_order_delivery_cancelled(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.CANCELLED,
    )
    mock_uow.orders.get_by_id.return_value = order

    result = await service.plan_order_delivery(order.id)
    assert result is None
