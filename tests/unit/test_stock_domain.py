from uuid import uuid4

from app.domain.entities.inventory import Stock


def test_stock_default_values():
    s = Stock(warehouse_id=uuid4(), product_id=uuid4())
    assert s.quantity == 0


def test_stock_custom_values():
    s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=100)
    assert s.quantity == 100


def test_stock_zero_quantity():
    s = Stock(warehouse_id=uuid4(), product_id=uuid4(), quantity=0)
    assert s.quantity == 0
