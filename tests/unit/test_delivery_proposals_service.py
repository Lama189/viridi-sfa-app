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
    return uow


@pytest.fixture
def mock_notifications_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_push_service():
    service = AsyncMock()
    return service


@pytest.fixture
def service(mock_uow, mock_notifications_service, mock_push_service):
    return DeliveryProposalService(
        mock_uow, mock_notifications_service, mock_push_service
    )


@pytest.mark.asyncio
async def test_process_assembled_order_success(
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
        status=OrderStatus.ASSEMBLED,
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
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = visit_plan

    expected_notification = Notification(
        id=uuid4(),
        employee_id=employee_id,
        title="Заказ готов к доставке",
        body="Тест",
        notification_type="order_delivery_proposal",
    )
    mock_notifications_service.create.return_value = expected_notification

    result = await service.process_assembled_order(order_id)

    assert result == expected_notification
    mock_notifications_service.create.assert_awaited_once()
    dto = mock_notifications_service.create.call_args[0][0]
    assert dto.employee_id == employee_id
    assert dto.notification_type == "order_delivery_proposal"
    assert "Корзинка" in dto.body
    assert dto.payload["order_id"] == str(order_id)
    assert dto.payload["retail_point_id"] == str(retail_point_id)
    assert dto.payload["visit_plan_id"] == str(plan_id)

    mock_push_service.send_to_employee.assert_awaited_once_with(
        employee_id=employee_id,
        title="Заказ готов к доставке",
        body=dto.body,
        data={
            "order_id": str(order_id),
            "retail_point_id": str(retail_point_id),
            "retail_point_name": "Супермаркет Корзинка",
            "visit_plan_id": str(plan_id),
            "plan_date": str(plan_date),
            "notification_type": "order_delivery_proposal",
        },
    )


@pytest.mark.asyncio
async def test_process_assembled_order_not_found(service, mock_uow):
    mock_uow.orders.get_by_id.return_value = None
    result = await service.process_assembled_order(uuid4())
    assert result is None


@pytest.mark.asyncio
async def test_process_assembled_order_not_assembled(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.PENDING,
    )
    mock_uow.orders.get_by_id.return_value = order

    result = await service.process_assembled_order(order.id)
    assert result is None


@pytest.mark.asyncio
async def test_process_assembled_order_no_assignment(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.ASSEMBLED,
    )
    mock_uow.orders.get_by_id.return_value = order
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = None

    result = await service.process_assembled_order(order.id)
    assert result is None


@pytest.mark.asyncio
async def test_process_assembled_order_no_visit_plan(service, mock_uow):
    order = Order(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        status=OrderStatus.ASSEMBLED,
    )
    mock_uow.orders.get_by_id.return_value = order

    assignment = RetailPointAssignment(
        retail_point_id=order.retail_point_id,
        employee_id=uuid4(),
    )
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment
    mock_uow.retail_points.get_by_id.return_value = None
    mock_uow.visit_plans.find_next_plan_for_retail_point.return_value = None

    result = await service.process_assembled_order(order.id)
    assert result is None
