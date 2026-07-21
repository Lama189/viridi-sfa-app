from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.stocks import StockCreateRequest, StockOperationRequest
from app.application.services.stocks import StockService
from app.domain.entities.inventory import Warehouse, Product
from app.domain.entities.stocks import Stock
from app.domain.enums import (
    StockTransactionType,
    TransactionActorType,
    StockReferenceType,
)


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.warehouses = AsyncMock()
    uow.products = AsyncMock()
    uow.stocks = AsyncMock()
    uow.stock_transactions = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return StockService(mock_uow)


def _warehouse(uid=None, is_active=True):
    return Warehouse(name="WH1", id=uid or uuid4(), is_active=is_active)


def _product(uid=None, is_active=True):
    return Product(
        category_id=uuid4(), name="NPK", price=Decimal("100.00"),
        id=uid or uuid4(), is_active=is_active,
    )


def _op_dto(warehouse_id=None, product_id=None, quantity=10, **overrides):
    defaults = dict(
        warehouse_id=warehouse_id or uuid4(),
        product_id=product_id or uuid4(),
        quantity=quantity,
        actor_type=TransactionActorType.EMPLOYEE,
        created_by_id=uuid4(),
        reference_type=StockReferenceType.ORDER,
        reference_id=uuid4(),
    )
    defaults.update(overrides)
    return StockOperationRequest(**defaults)


# ---------------------------------------------------------------------------
# create_stock
# ---------------------------------------------------------------------------

class TestStockServiceCreate:
    @pytest.mark.asyncio
    async def test_create_stock_success(self, service, mock_uow):
        wid, pid = uuid4(), uuid4()
        mock_uow.warehouses.get_by_id.return_value = _warehouse(uid=wid)
        mock_uow.products.get_by_id.return_value = _product(uid=pid)
        mock_uow.stocks.get.return_value = None

        dto = StockCreateRequest(warehouse_id=wid, product_id=pid)
        result = await service.create_stock(dto)

        assert result.warehouse_id == wid
        assert result.product_id == pid
        assert result.quantity == 0
        mock_uow.stocks.add.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_stock_already_exists(self, service, mock_uow):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.products.get_by_id.return_value = _product()
        mock_uow.stocks.get.return_value = Stock(warehouse_id=uuid4(), product_id=uuid4())

        dto = StockCreateRequest(warehouse_id=uuid4(), product_id=uuid4())
        with pytest.raises(ValueError, match="already exists"):
            await service.create_stock(dto)

    @pytest.mark.asyncio
    async def test_create_stock_warehouse_not_found(self, service, mock_uow):
        mock_uow.warehouses.get_by_id.return_value = None
        dto = StockCreateRequest(warehouse_id=uuid4(), product_id=uuid4())
        with pytest.raises(ValueError, match="Warehouse"):
            await service.create_stock(dto)

    @pytest.mark.asyncio
    async def test_create_stock_warehouse_inactive(self, service, mock_uow):
        mock_uow.warehouses.get_by_id.return_value = _warehouse(is_active=False)
        dto = StockCreateRequest(warehouse_id=uuid4(), product_id=uuid4())
        with pytest.raises(ValueError, match="inactive"):
            await service.create_stock(dto)

    @pytest.mark.asyncio
    async def test_create_stock_product_not_found(self, service, mock_uow):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.products.get_by_id.return_value = None
        dto = StockCreateRequest(warehouse_id=uuid4(), product_id=uuid4())
        with pytest.raises(ValueError, match="Product"):
            await service.create_stock(dto)

    @pytest.mark.asyncio
    async def test_create_stock_product_inactive(self, service, mock_uow):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.products.get_by_id.return_value = _product(is_active=False)
        dto = StockCreateRequest(warehouse_id=uuid4(), product_id=uuid4())
        with pytest.raises(ValueError, match="inactive"):
            await service.create_stock(dto)


# ---------------------------------------------------------------------------
# add_stock
# ---------------------------------------------------------------------------

class TestStockServiceAdd:
    @pytest.mark.asyncio
    async def test_add_stock_success(self, service, mock_uow):
        wid, pid = uuid4(), uuid4()
        stock = Stock(warehouse_id=wid, product_id=pid, quantity=10)
        mock_uow.warehouses.get_by_id.return_value = _warehouse(uid=wid)
        mock_uow.products.get_by_id.return_value = _product(uid=pid)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(warehouse_id=wid, product_id=pid, quantity=5)
        result = await service.add_stock(dto)

        assert result.quantity == 15
        mock_uow.stocks.update.assert_awaited_once()
        mock_uow.stock_transactions.add.assert_awaited_once()
        mock_uow.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_add_stock_warehouse_not_found(self, service, mock_uow):
        mock_uow.warehouses.get_by_id.return_value = None
        dto = _op_dto()
        with pytest.raises(ValueError, match="Warehouse"):
            await service.add_stock(dto)

    @pytest.mark.asyncio
    async def test_add_stock_product_not_found(self, service, mock_uow):
        mock_uow.warehouses.get_by_id.return_value = _warehouse()
        mock_uow.products.get_by_id.return_value = None
        dto = _op_dto()
        with pytest.raises(ValueError, match="Product"):
            await service.add_stock(dto)


# ---------------------------------------------------------------------------
# reserve_stock
# ---------------------------------------------------------------------------

class TestStockServiceReserve:
    @pytest.mark.asyncio
    async def test_reserve_success(self, service, mock_uow):
        wid, pid = uuid4(), uuid4()
        stock = Stock(warehouse_id=wid, product_id=pid, quantity=50)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(warehouse_id=wid, product_id=pid, quantity=10)
        result = await service.reserve_stock(dto)

        assert result.quantity == 50
        assert result.reserved_quantity == 10
        mock_uow.stocks.update.assert_awaited_once()
        tx_call = mock_uow.stock_transactions.add.call_args[0][0]
        assert tx_call.transaction_type == StockTransactionType.RESERVATION

    @pytest.mark.asyncio
    async def test_reserve_insufficient_stock(self, service, mock_uow):
        stock = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=5)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(quantity=10)
        with pytest.raises(ValueError, match="Insufficient stock"):
            await service.reserve_stock(dto)


# ---------------------------------------------------------------------------
# release_reservation
# ---------------------------------------------------------------------------

class TestStockServiceRelease:
    @pytest.mark.asyncio
    async def test_release_success(self, service, mock_uow):
        wid, pid = uuid4(), uuid4()
        stock = Stock(warehouse_id=wid, product_id=pid, quantity=50, reserved_quantity=20)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(warehouse_id=wid, product_id=pid, quantity=10)
        result = await service.release_reservation(dto)

        assert result.reserved_quantity == 10
        tx_call = mock_uow.stock_transactions.add.call_args[0][0]
        assert tx_call.transaction_type == StockTransactionType.CANCEL_RESERVATION

    @pytest.mark.asyncio
    async def test_release_exceeds_reservation(self, service, mock_uow):
        stock = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=5)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(quantity=10)
        with pytest.raises(ValueError, match="Insufficient reservation"):
            await service.release_reservation(dto)


# ---------------------------------------------------------------------------
# confirm_sale
# ---------------------------------------------------------------------------

class TestStockServiceConfirmSale:
    @pytest.mark.asyncio
    async def test_confirm_sale_success(self, service, mock_uow):
        wid, pid = uuid4(), uuid4()
        stock = Stock(warehouse_id=wid, product_id=pid, quantity=50, reserved_quantity=20)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(warehouse_id=wid, product_id=pid, quantity=10)
        result = await service.confirm_sale(dto)

        assert result.quantity == 40
        assert result.reserved_quantity == 10
        tx_call = mock_uow.stock_transactions.add.call_args[0][0]
        assert tx_call.transaction_type == StockTransactionType.SALE
        assert tx_call.quantity_delta == -10

    @pytest.mark.asyncio
    async def test_confirm_sale_insufficient_reservation(self, service, mock_uow):
        stock = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=5)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(quantity=10)
        with pytest.raises(ValueError, match="Insufficient reservation"):
            await service.confirm_sale(dto)


# ---------------------------------------------------------------------------
# write_off
# ---------------------------------------------------------------------------

class TestStockServiceWriteOff:
    @pytest.mark.asyncio
    async def test_write_off_success(self, service, mock_uow):
        wid, pid = uuid4(), uuid4()
        stock = Stock(warehouse_id=wid, product_id=pid, quantity=50)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(warehouse_id=wid, product_id=pid, quantity=15)
        result = await service.write_off(dto)

        assert result.quantity == 35
        tx_call = mock_uow.stock_transactions.add.call_args[0][0]
        assert tx_call.transaction_type == StockTransactionType.WRITEOFF
        assert tx_call.quantity_delta == -15

    @pytest.mark.asyncio
    async def test_write_off_insufficient(self, service, mock_uow):
        stock = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=5, reserved_quantity=3)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(quantity=5)
        with pytest.raises(ValueError, match="Insufficient stock"):
            await service.write_off(dto)


# ---------------------------------------------------------------------------
# return_stock
# ---------------------------------------------------------------------------

class TestStockServiceReturn:
    @pytest.mark.asyncio
    async def test_return_success(self, service, mock_uow):
        wid, pid = uuid4(), uuid4()
        stock = Stock(warehouse_id=wid, product_id=pid, quantity=50)
        mock_uow.stocks.get_for_update.return_value = stock

        dto = _op_dto(warehouse_id=wid, product_id=pid, quantity=10)
        result = await service.return_stock(dto)

        assert result.quantity == 60
        tx_call = mock_uow.stock_transactions.add.call_args[0][0]
        assert tx_call.transaction_type == StockTransactionType.RETURN
        assert tx_call.quantity_delta == 10

    @pytest.mark.asyncio
    async def test_return_stock_not_found(self, service, mock_uow):
        mock_uow.stocks.get_for_update.return_value = None

        dto = _op_dto()
        with pytest.raises(ValueError, match="not found"):
            await service.return_stock(dto)
