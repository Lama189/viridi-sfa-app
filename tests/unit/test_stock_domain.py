from uuid import uuid4

import pytest

from app.core.exceptions import (
    InsufficientReservationError,
    InsufficientReservedStockError,
    InsufficientStockError,
)
from app.domain.entities.stocks import Stock, StockTransaction
from app.domain.enums import (
    StockReferenceType,
    StockTransactionType,
    TransactionActorType,
)

# ---------------------------------------------------------------------------
# Stock — creation & validation
# ---------------------------------------------------------------------------


class TestStockCreation:
    def test_defaults(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4())
        assert s.quantity == 0
        assert s.reserved_quantity == 0
        assert s.updated_at is not None

    def test_custom_values(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=100, reserved_quantity=20
        )
        assert s.quantity == 100
        assert s.reserved_quantity == 20

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=-1)

    def test_negative_reserved_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            Stock(
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity=10,
                reserved_quantity=-1,
            )

    def test_reserved_exceeds_quantity_raises(self):
        with pytest.raises(ValueError, match="cannot exceed"):
            Stock(
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity=5,
                reserved_quantity=10,
            )


# ---------------------------------------------------------------------------
# Stock — available_quantity
# ---------------------------------------------------------------------------


class TestStockAvailable:
    def test_no_reserved(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        assert s.available_quantity == 50

    def test_with_reserved(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=20
        )
        assert s.available_quantity == 30

    def test_fully_reserved(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=10, reserved_quantity=10
        )
        assert s.available_quantity == 0


# ---------------------------------------------------------------------------
# Stock — increase
# ---------------------------------------------------------------------------


class TestStockIncrease:
    def test_increase(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=10)
        s.increase(5)
        assert s.quantity == 15

    def test_increase_zero_raises(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=10)
        with pytest.raises(ValueError, match="positive"):
            s.increase(0)

    def test_increase_negative_raises(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=10)
        with pytest.raises(ValueError, match="positive"):
            s.increase(-3)


# ---------------------------------------------------------------------------
# Stock — reserve
# ---------------------------------------------------------------------------


class TestStockReserve:
    def test_reserve(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        s.reserve(10)
        assert s.quantity == 50
        assert s.reserved_quantity == 10

    def test_reserve_all(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        s.reserve(50)
        assert s.available_quantity == 0

    def test_reserve_zero_raises(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=10)
        with pytest.raises(ValueError, match="positive"):
            s.reserve(0)

    def test_reserve_insufficient_stock_raises(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=10, reserved_quantity=5
        )
        with pytest.raises(InsufficientStockError):
            s.reserve(10)

    def test_reserve_cumulative(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        s.reserve(10)
        s.reserve(20)
        assert s.reserved_quantity == 30
        assert s.available_quantity == 20


# ---------------------------------------------------------------------------
# Stock — release_reservation
# ---------------------------------------------------------------------------


class TestStockRelease:
    def test_release(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=20
        )
        s.release_reservation(10)
        assert s.reserved_quantity == 10

    def test_release_all(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=20
        )
        s.release_reservation(20)
        assert s.reserved_quantity == 0

    def test_release_zero_raises(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=20
        )
        with pytest.raises(ValueError, match="positive"):
            s.release_reservation(0)

    def test_release_exceeds_reservation_raises(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=5
        )
        with pytest.raises(InsufficientReservedStockError):
            s.release_reservation(10)


# ---------------------------------------------------------------------------
# Stock — sell
# ---------------------------------------------------------------------------


class TestStockSell:
    def test_sell(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=20
        )
        s.sell(10)
        assert s.quantity == 40
        assert s.reserved_quantity == 10

    def test_sell_all_reserved(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=20
        )
        s.sell(20)
        assert s.quantity == 30
        assert s.reserved_quantity == 0

    def test_sell_zero_raises(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=20
        )
        with pytest.raises(ValueError, match="positive"):
            s.sell(0)

    def test_sell_exceeds_reservation_raises(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=5
        )
        with pytest.raises(InsufficientReservationError):
            s.sell(10)


# ---------------------------------------------------------------------------
# Stock — write_off
# ---------------------------------------------------------------------------


class TestStockWriteOff:
    def test_write_off(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        s.write_off(15)
        assert s.quantity == 35

    def test_write_off_zero_raises(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        with pytest.raises(ValueError, match="positive"):
            s.write_off(0)

    def test_write_off_insufficient_stock_raises(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=5, reserved_quantity=3
        )
        with pytest.raises(InsufficientStockError):
            s.write_off(5)

    def test_write_off_available_only(self):
        s = Stock(
            warehouse_id=uuid4(), product_id=uuid4(), quantity=50, reserved_quantity=30
        )
        s.write_off(20)
        assert s.quantity == 30
        assert s.reserved_quantity == 30


# ---------------------------------------------------------------------------
# Stock — return_product
# ---------------------------------------------------------------------------


class TestStockReturn:
    def test_return(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        s.return_product(10)
        assert s.quantity == 60

    def test_return_zero_raises(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        with pytest.raises(ValueError, match="positive"):
            s.return_product(0)

    def test_return_negative_raises(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=50)
        with pytest.raises(ValueError, match="positive"):
            s.return_product(-5)


# ---------------------------------------------------------------------------
# Stock — _touch
# ---------------------------------------------------------------------------


class TestStockTouch:
    def test_touch_updates_timestamp(self):
        s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=10)
        old = s.updated_at
        s.increase(1)
        assert s.updated_at >= old


# ---------------------------------------------------------------------------
# StockTransaction
# ---------------------------------------------------------------------------


class TestStockTransaction:
    def test_create_basic(self):
        tx = StockTransaction(
            warehouse_id=uuid4(),
            product_id=uuid4(),
            quantity_delta=10,
            transaction_type=StockTransactionType.RECEIPT,
            reference_type=StockReferenceType.ORDER,
            reference_id=uuid4(),
        )
        assert isinstance(tx.id, type(uuid4()))
        assert tx.quantity_delta == 10
        assert tx.transaction_type == StockTransactionType.RECEIPT
        assert tx.actor_type == TransactionActorType.SYSTEM
        assert tx.created_by_id is None

    def test_create_with_actor(self):
        uid = uuid4()
        tx = StockTransaction(
            warehouse_id=uuid4(),
            product_id=uuid4(),
            quantity_delta=-5,
            transaction_type=StockTransactionType.SALE,
            reference_type=StockReferenceType.ORDER,
            reference_id=uuid4(),
            actor_type=TransactionActorType.CLIENT,
            created_by_id=uid,
        )
        assert tx.actor_type == TransactionActorType.CLIENT
        assert tx.created_by_id == uid

    def test_negative_delta_allowed(self):
        tx = StockTransaction(
            warehouse_id=uuid4(),
            product_id=uuid4(),
            quantity_delta=-20,
            transaction_type=StockTransactionType.WRITEOFF,
            reference_type=StockReferenceType.WRITEOFF,
            reference_id=uuid4(),
        )
        assert tx.quantity_delta == -20

    def test_all_transaction_types(self):
        for tx_type in StockTransactionType:
            tx = StockTransaction(
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity_delta=1,
                transaction_type=tx_type,
                reference_type=StockReferenceType.ORDER,
                reference_id=uuid4(),
            )
            assert tx.transaction_type == tx_type

    def test_all_reference_types(self):
        for ref_type in StockReferenceType:
            tx = StockTransaction(
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity_delta=1,
                transaction_type=StockTransactionType.RECEIPT,
                reference_type=ref_type,
                reference_id=uuid4(),
            )
            assert tx.reference_type == ref_type

    def test_all_actor_types(self):
        for actor_type in TransactionActorType:
            tx = StockTransaction(
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity_delta=1,
                transaction_type=StockTransactionType.ADJUSTMENT,
                reference_type=StockReferenceType.INVENTORY,
                reference_id=uuid4(),
                actor_type=actor_type,
            )
            assert tx.actor_type == actor_type
