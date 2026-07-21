from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.extensions import UserNotFoundError
from app.api.v1.schemas.orders import CreateOrderRequest, OrderItemCreateRequest
from app.api.v1.schemas.stocks import StockOperationRequest
from app.application.services.orders import OrdersService
from app.domain.entities.inventory import Warehouse, Product
from app.domain.entities.clients import Client
from app.domain.entities.retail_points import RetailPoint
from app.domain.enums import OrderStatus


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.warehouses = AsyncMock()
    uow.clients = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.products = AsyncMock()
    uow.orders = AsyncMock()
    uow.order_items = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_stocks():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_stocks):
    return OrdersService(mock_uow, mock_stocks)


def _warehouse(uid=None, is_active=True):
    return Warehouse(name="WH1", id=uid or uuid4(), is_active=is_active)


def _client(uid=None, is_active=True):
    return Client(phone="+998900000000", full_name="Test Client", id=uid or uuid4(), is_active=is_active)


def _retail_point(uid=None, is_active=True):
    return RetailPoint(name="RP1", address="Addr", id=uid or uuid4(), is_active=is_active)


def _product(name="NPK-10", price=Decimal("150.00"), uid=None, is_active=True, volume=Decimal("1.000")):
    return Product(
        category_id=uuid4(), name=name, price=price, id=uid or uuid4(),
        is_active=is_active, volume=volume,
    )


def _create_dto(warehouse_id, retail_point_id, items):
    return CreateOrderRequest(
        warehouse_id=warehouse_id,
        retail_point_id=retail_point_id,
        items=[OrderItemCreateRequest(product_id=pid, quantity=q) for pid, q in items],
    )


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
        mock_stocks.reserve_stock.assert_awaited_once()

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

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(UserNotFoundError):
            await service.create(uuid4(), dto)

    @pytest.mark.asyncio
    async def test_create_client_inactive(self, service, mock_uow, mock_stocks):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client(is_active=False)

        dto = _create_dto(uuid4(), uuid4(), [(uuid4(), 1)])
        with pytest.raises(UserNotFoundError):
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
        p1 = _product(name="A", price=Decimal("100.00"), uid=pid1, volume=Decimal("0.500"))
        p2 = _product(name="B", price=Decimal("200.00"), uid=pid2, volume=Decimal("1.500"))

        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.clients.get_by_id.return_value = _client()
        mock_uow.retail_points.get_by_id.return_value = _retail_point()
        mock_uow.products.list_by_ids.return_value = [p1, p2]

        dto = _create_dto(uuid4(), uuid4(), [(pid1, 2), (pid2, 3)])
        result = await service.create(uuid4(), dto)

        assert len(result.items) == 2
        assert mock_stocks.reserve_stock.await_count == 2


# ---------------------------------------------------------------------------
# confirm
# ---------------------------------------------------------------------------

class TestOrdersServiceConfirm:
    @pytest.mark.asyncio
    async def test_confirm_success(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        pid = uuid4()
        order = _pending_order_with_item(oid, pid)
        mock_uow.orders.get_by_id.return_value = order

        result = await service.confirm(oid)
        assert result.status == OrderStatus.CONFIRMED
        mock_stocks.confirm_sale.assert_awaited_once()
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
        mock_stocks.release_reservation.assert_awaited_once()
        mock_uow.orders.update.assert_awaited_once()
        mock_uow.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_cancel_not_found(self, service, mock_uow, mock_stocks):
        mock_uow.orders.get_by_id.return_value = None
        with pytest.raises(ValueError, match="not found"):
            await service.cancel(uuid4())

    @pytest.mark.asyncio
    async def test_cancel_non_pending(self, service, mock_uow, mock_stocks):
        oid = uuid4()
        order = _pending_order_with_item(oid)
        order.status = OrderStatus.CONFIRMED
        mock_uow.orders.get_by_id.return_value = order
        with pytest.raises(ValueError, match="Cannot confirm"):
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
        with pytest.raises(ValueError, match="Cannot confirm"):
            await service.ship(oid)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _pending_order_with_item(order_id=None, product_id=None):
    from app.domain.entities.orders import Order, OrderItem
    oid = order_id or uuid4()
    pid = product_id or uuid4()
    order = Order(
        warehouse_id=uuid4(), created_by_id=uuid4(), retail_point_id=uuid4(),
        id=oid,
    )
    item = OrderItem(
        order_id=oid, product_id=pid, quantity=10,
        price_at_order=Decimal("5000.00"), total_volume=Decimal("0.100"),
    )
    order.add_item(item)
    return order
