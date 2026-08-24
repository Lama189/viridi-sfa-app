from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.dto.orders import OrderCreateDTO, OrderItemCreateDTO
from app.application.services.orders import OrdersService
from app.core.exceptions import UserNotActiveError, UserNotFoundError
from app.domain.entities.clients import Client
from app.domain.entities.inventory import Product, Warehouse
from app.domain.entities.retail_points import RetailPoint
from app.domain.enums import OrderStatus


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.warehouses = AsyncMock()
    uow.clients = AsyncMock()
    uow.employees = AsyncMock()
    uow.employees.get_by_id.return_value = None
    uow.retail_points = AsyncMock()
    uow.products = AsyncMock()
    uow.orders = AsyncMock()
    uow.order_items = AsyncMock()
    uow.outbox = AsyncMock()
    uow.retail_point_assignments = AsyncMock()
    uow.visit_plans = AsyncMock()
    uow.visits = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_stocks():
    return AsyncMock()


@pytest.fixture
def mock_delivery_assignment_service():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_stocks, mock_delivery_assignment_service):
    return OrdersService(
        uow=mock_uow,
        stocks=mock_stocks,
        delivery_assignment_service=mock_delivery_assignment_service,
    )


def _warehouse(uid=None, is_active=True):
    return Warehouse(name="WH1", id=uid or uuid4(), is_active=is_active)


def _client(uid=None, is_active=True):
    return Client(
        phone="+998900000000",
        full_name="Test Client",
        id=uid or uuid4(),
        is_active=is_active,
    )


def _employee(uid=None, is_active=True):
    from app.domain.entities.employees import Employee
    from app.domain.enums import EmployeeRole

    return Employee(
        phone="+998901112233",
        password_hash="hash",
        full_name="Agent Tester",
        role=EmployeeRole.AGENT,
        id=uid or uuid4(),
        is_active=is_active,
    )


def _retail_point(uid=None, is_active=True):
    return RetailPoint(
        name="RP1", address="Addr", id=uid or uuid4(), is_active=is_active
    )


def _product(
    name="NPK-10",
    price=Decimal("150.00"),
    uid=None,
    is_active=True,
    volume=Decimal("1.000"),
):
    return Product(
        category_id=uuid4(),
        name=name,
        price=price,
        id=uid or uuid4(),
        is_active=is_active,
        volume=volume,
    )


def _create_dto(warehouse_id, retail_point_id, items):
    return OrderCreateDTO(
        warehouse_id=warehouse_id,
        retail_point_id=retail_point_id,
        items=[OrderItemCreateDTO(product_id=pid, quantity=q) for pid, q in items],
    )


# ---------------------------------------------------------------------------
# read methods
# ---------------------------------------------------------------------------


class TestOrdersServiceRead:
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_uow):
        oid = uuid4()
        order = _pending_order_with_item(oid)
        mock_uow.orders.get_by_id.return_value = order

        res = await service.get_by_id(oid)
        assert res == order
        mock_uow.orders.get_by_id.assert_awaited_once_with(oid)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service, mock_uow):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.get_by_id(uuid4())

    @pytest.mark.asyncio
    async def test_list_orders(self, service, mock_uow):
        orders = [_pending_order_with_item()]
        mock_uow.orders.list.return_value = orders

        res = await service.list_orders(
            statuses=[OrderStatus.PENDING], limit=10, offset=0
        )
        assert res == orders
        mock_uow.orders.list.assert_awaited_once_with(
            statuses=[OrderStatus.PENDING], limit=10, offset=0
        )

    @pytest.mark.asyncio
    async def test_list_by_client(self, service, mock_uow):
        cid = uuid4()
        orders = [_pending_order_with_item()]
        mock_uow.orders.list_by_client.return_value = orders

        res = await service.list_by_client(cid, statuses=[OrderStatus.PENDING])
        assert res == orders
        mock_uow.orders.list_by_client.assert_awaited_once_with(
            cid, statuses=[OrderStatus.PENDING]
        )

    @pytest.mark.asyncio
    async def test_list_by_retail_point(self, service, mock_uow):
        rpid = uuid4()
        orders = [_pending_order_with_item()]
        mock_uow.orders.list_by_retail_point.return_value = orders

        res = await service.list_by_retail_point(rpid)
        assert res == orders
        mock_uow.orders.list_by_retail_point.assert_awaited_once_with(
            rpid, statuses=None
        )

    @pytest.mark.asyncio
    async def test_list_by_client_retail_point(self, service, mock_uow):
        cid = uuid4()
        rpid = uuid4()
        from app.domain.entities.retail_point_members import RetailPointMember

        mock_uow.retail_point_members.get_by_client_id.return_value = [
            RetailPointMember(retail_point_id=rpid, client_id=cid)
        ]
        orders = [_pending_order_with_item()]
        mock_uow.orders.list_by_retail_points.return_value = orders

        res = await service.list_by_client_retail_point(
            cid, statuses=[OrderStatus.PENDING]
        )
        assert res == orders
        mock_uow.retail_point_members.get_by_client_id.assert_awaited_once_with(cid)
        mock_uow.orders.list_by_retail_points.assert_awaited_once_with(
            [rpid], statuses=[OrderStatus.PENDING]
        )

    @pytest.mark.asyncio
    async def test_get_counts_by_status(self, service, mock_uow):
        counts = {OrderStatus.PENDING: 3, OrderStatus.DELIVERED: 10}
        mock_uow.orders.get_counts_by_status.return_value = counts

        res = await service.get_counts_by_status()
        assert res == counts
        mock_uow.orders.get_counts_by_status.assert_awaited_once_with(employee_id=None)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------


class TestOrdersServiceCreate:
    @pytest.mark.asyncio
    async def test_create_success(self, service, mock_uow, mock_stocks):
        wid, cid, rpid = uuid4(), uuid4(), uuid4()
        pid = uuid4()
        product = _product(uid=pid)

        mock_uow.warehouses.get_by_id.return_value = _warehouse(uid=wid)
        mock_uow.clients.get_by_id.return_value = _client(uid=cid)
        mock_uow.retail_points.get_by_id.return_value = _retail_point(uid=rpid)
        mock_uow.products.list_by_ids.return_value = [product]

        dto = _create_dto(wid, rpid, [(pid, 5)])
        result = await service.create(cid, dto)

        assert result.warehouse_id == wid
        assert result.created_by_id == cid
        assert result.retail_point_id == rpid
        assert result.status == OrderStatus.PENDING
        assert len(result.items) == 1
        assert result.items[0].quantity == 5
        mock_uow.orders.add.assert_awaited_once()
        mock_uow.order_items.add.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()
        mock_stocks.reserve_stocks_batch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_by_employee_success(self, service, mock_uow, mock_stocks):
        wid, eid, rpid = uuid4(), uuid4(), uuid4()
        pid = uuid4()
        product = _product(uid=pid)

        mock_uow.warehouses.get_by_id.return_value = _warehouse(uid=wid)
        mock_uow.clients.get_by_id.return_value = None
        mock_uow.employees.get_by_id.return_value = _employee(uid=eid)
        mock_uow.retail_points.get_by_id.return_value = _retail_point(uid=rpid)
        mock_uow.products.list_by_ids.return_value = [product]

        dto = _create_dto(wid, rpid, [(pid, 3)])
        result = await service.create(eid, dto)

        assert result.warehouse_id == wid
        assert result.created_by_id == eid
        assert result.retail_point_id == rpid
        assert result.status == OrderStatus.PENDING
        assert len(result.items) == 1
        assert result.items[0].quantity == 3
        mock_uow.orders.add.assert_awaited_once()
        mock_uow.order_items.add.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()
        mock_stocks.reserve_stocks_batch.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_warehouse_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = None

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(ValueError, match="Warehouse"):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_warehouse_inactive(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse(is_active=False)

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(ValueError, match="inactive"):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_client_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = None
        mock_uow.employees.get_by_id.return_value = None

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(UserNotFoundError):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_client_inactive(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client(is_active=False)

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(UserNotActiveError):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_employee_inactive(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = None
        mock_uow.employees.get_by_id.return_value = _employee(is_active=False)

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(UserNotActiveError):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_retail_point_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client()
        mock_uow.retail_points.get_by_id.return_value = None

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(ValueError, match="Retail Point"):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_retail_point_inactive(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client()
        mock_uow.retail_points.get_by_id.return_value = _retail_point(is_active=False)

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(ValueError, match="inactive"):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_product_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client()
        mock_uow.retail_points.get_by_id.return_value = _retail_point()
        mock_uow.products.list_by_ids.return_value = []

        pid = uuid4()
        dto = _create_dto(uuid4(), uuid4(), [(pid, 1)])
        with pytest.raises(ValueError, match="not found"):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_product_inactive(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client()
        mock_uow.retail_points.get_by_id.return_value = _retail_point()
        inactive_product = _product(is_active=False)
        mock_uow.products.list_by_ids.return_value = [inactive_product]

        dto = _create_dto(uuid4(), uuid4(), [(inactive_product.id, 1)])
        with pytest.raises(ValueError, match="inactive"):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_multiple_items(self, service, mock_uow, mock_stocks):
        pid1, pid2 = uuid4(), uuid4()
        p1 = _product(
            name="A", price=Decimal("100.00"), uid=pid1, volume=Decimal("0.500")
        )
        p2 = _product(
            name="B", price=Decimal("200.00"), uid=pid2, volume=Decimal("1.500")
        )

        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client()
        mock_uow.retail_points.get_by_id.return_value = _retail_point()
        mock_uow.products.list_by_ids.return_value = [p1, p2]

        dto = _create_dto(uuid4(), uuid4(), [(pid1, 2), (pid2, 3)])
        result = await service.create(uuid4(), dto)

        assert len(result.items) == 2
        mock_stocks.reserve_stocks_batch.assert_awaited_once()


# ---------------------------------------------------------------------------
# confirm
# ---------------------------------------------------------------------------


class TestOrdersServiceConfirm:
    @pytest.mark.asyncio
    async def test_confirm_success(
        self, service, mock_uow, mock_delivery_assignment_service
    ):
        oid = uuid4()
        pid = uuid4()
        order = _pending_order_with_item(oid, pid)
        mock_uow.orders.get_by_id.return_value = order

        result = await service.confirm(oid)
        assert result.status == OrderStatus.CONFIRMED
        mock_delivery_assignment_service.assign_order_to_next_visit.assert_awaited_once_with(
            order
        )
        mock_uow.orders.update.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_confirm_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.confirm(uuid4())

    @pytest.mark.asyncio
    async def test_confirm_non_pending(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        order = _pending_order_with_item(oid)
        order.status = OrderStatus.CONFIRMED
        mock_uow.orders.get_by_id.return_value = order
        with pytest.raises(ValueError, match="Cannot confirm"):
            await service.confirm(oid)


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------


class TestOrdersServiceCancel:
    @pytest.mark.asyncio
    async def test_cancel_success(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        pid = uuid4()
        order = _pending_order_with_item(oid, pid)
        mock_uow.orders.get_by_id.return_value = order

        result = await service.cancel(oid)
        assert result.status == OrderStatus.CANCELLED
        mock_stocks.release_reservations_batch.assert_awaited_once()
        mock_uow.orders.update.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.cancel(uuid4())

    @pytest.mark.asyncio
    async def test_cancel_shipped(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        order = _pending_order_with_item(oid)
        order.status = OrderStatus.SHIPPED
        mock_uow.orders.get_by_id.return_value = order
        with pytest.raises(ValueError, match="Cannot cancel"):
            await service.cancel(oid)


# ---------------------------------------------------------------------------
# ship
# ---------------------------------------------------------------------------


class TestOrdersServiceShip:
    @pytest.mark.asyncio
    async def test_ship_success(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        order = _pending_order_with_item(oid)
        order.status = OrderStatus.CONFIRMED
        mock_uow.orders.get_by_id.return_value = order

        result = await service.ship(oid)
        assert result.status == OrderStatus.SHIPPED
        mock_uow.orders.update.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ship_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.ship(uuid4())

    @pytest.mark.asyncio
    async def test_ship_non_confirmed(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        order = _pending_order_with_item(oid)
        mock_uow.orders.get_by_id.return_value = order
        with pytest.raises(ValueError, match="Cannot ship"):
            await service.ship(oid)


# ---------------------------------------------------------------------------
# start_assembly
# ---------------------------------------------------------------------------


class TestOrdersServiceStartAssembly:
    @pytest.mark.asyncio
    async def test_start_assembly_success(self, service, mock_uow):
        oid = uuid4()
        emp_id = uuid4()
        order = _pending_order_with_item(oid)
        mock_uow.orders.get_by_id.return_value = order

        result = await service.start_assembly(oid, employee_id=emp_id)
        assert result.status == OrderStatus.ASSEMBLY_STARTED
        mock_uow.orders.update.assert_awaited_once_with(order)
        mock_uow.outbox.add.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_start_assembly_not_found(self, service, mock_uow):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.start_assembly(uuid4())


# ---------------------------------------------------------------------------
# deliver
# ---------------------------------------------------------------------------


class TestOrdersServiceDeliver:
    @pytest.mark.asyncio
    async def test_deliver_success(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        pid = uuid4()
        emp_id = uuid4()
        order = _pending_order_with_item(oid, pid)
        order.status = OrderStatus.SHIPPED
        mock_uow.orders.get_by_id.return_value = order

        result = await service.deliver(oid, employee_id=emp_id)
        assert result.status == OrderStatus.DELIVERED
        mock_stocks.confirm_sales_batch.assert_awaited_once()
        mock_uow.orders.update.assert_awaited_once_with(order)
        mock_uow.outbox.add.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_deliver_not_found(self, service, mock_uow):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.deliver(uuid4())


# ---------------------------------------------------------------------------
# load_order & load_today_orders
# ---------------------------------------------------------------------------


class TestOrdersServiceLoad:
    @pytest.mark.asyncio
    async def test_load_order_success(self, service, mock_uow):
        oid = uuid4()
        emp_id = uuid4()
        order = _pending_order_with_item(oid)
        order.status = OrderStatus.ASSEMBLED
        mock_uow.orders.get_by_id.return_value = order

        result = await service.load_order(oid, employee_id=emp_id)
        assert result.status == OrderStatus.LOADED
        mock_uow.orders.update.assert_awaited_once_with(order)
        mock_uow.outbox.add.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_load_order_not_found(self, service, mock_uow):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.load_order(uuid4(), employee_id=uuid4())

    @pytest.mark.asyncio
    async def test_load_order_invalid_status(self, service, mock_uow):
        oid = uuid4()
        order = _pending_order_with_item(oid)
        order.status = OrderStatus.PENDING
        mock_uow.orders.get_by_id.return_value = order

        with pytest.raises(ValueError, match="Cannot load order"):
            await service.load_order(oid, employee_id=uuid4())

    @pytest.mark.asyncio
    async def test_load_today_orders_success(self, service, mock_uow):
        from datetime import date

        from app.domain.entities.visit_plans import VisitPlan
        from app.domain.enums import VisitPlanStatus

        emp_id = uuid4()
        plan = VisitPlan(
            id=uuid4(),
            employee_id=emp_id,
            plan_date=date.today(),
            status=VisitPlanStatus.PLANNED,
        )
        mock_uow.visit_plans.get_by_employee_and_date.return_value = plan

        order1 = _pending_order_with_item()
        order1.status = OrderStatus.ASSEMBLED
        mock_uow.orders.list_by_planned_visit.return_value = [order1]

        result = await service.load_today_orders(emp_id)
        assert len(result) == 1
        assert result[0].status == OrderStatus.LOADED
        mock_uow.orders.update.assert_awaited_once_with(order1)
        mock_uow.commit.assert_awaited_once()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _pending_order_with_item(order_id=None, product_id=None):
    from app.domain.entities.orders import Order, OrderItem

    oid = order_id or uuid4()
    pid = product_id or uuid4()
    order = Order(
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        id=oid,
    )
    item = OrderItem(
        order_id=oid,
        product_id=pid,
        quantity=10,
        price_at_order=Decimal("5000.00"),
        total_volume=Decimal("0.100"),
    )
    order.add_item(item)
    return order
