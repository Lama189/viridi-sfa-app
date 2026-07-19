from decimal import Decimal
from uuid import uuid4

from app.domain.entities.orders import Order, OrderItem
from app.domain.enums import OrderStatus


def test_order_default_values():
    order = Order(warehouse_id=uuid4(), created_by_id=uuid4(), retail_point_id=uuid4())
    assert isinstance(order.id, type(uuid4()))
    assert order.visit_id is None
    assert order.status == OrderStatus.PENDING
    assert order.total_amount == Decimal("0.00")
    assert order.total_volume == Decimal("0.000")


def test_order_custom_values():
    order_id = uuid4()
    visit_id = uuid4()
    order = Order(
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=uuid4(),
        id=order_id,
        visit_id=visit_id,
        status=OrderStatus.CONFIRMED,
        total_amount=Decimal("150000.00"),
        total_volume=Decimal("0.500"),
    )
    assert order.id == order_id
    assert order.visit_id == visit_id
    assert order.status == OrderStatus.CONFIRMED
    assert order.total_amount == Decimal("150000.00")
    assert order.total_volume == Decimal("0.500")


def test_order_status_pending():
    order = Order(warehouse_id=uuid4(), created_by_id=uuid4(), retail_point_id=uuid4())
    assert order.status == OrderStatus.PENDING


def test_order_status_transitions():
    order = Order(warehouse_id=uuid4(), created_by_id=uuid4(), retail_point_id=uuid4())
    order.status = OrderStatus.CONFIRMED
    assert order.status == OrderStatus.CONFIRMED
    order.status = OrderStatus.SHIPPED
    assert order.status == OrderStatus.SHIPPED
    order.status = OrderStatus.CANCELLED
    assert order.status == OrderStatus.CANCELLED


def test_order_item_default_values():
    item = OrderItem(
        order_id=uuid4(),
        product_id=uuid4(),
        quantity=10,
        price_at_order=Decimal("5000.00"),
        total_volume=Decimal("0.100"),
    )
    assert item.quantity == 10
    assert item.price_at_order == Decimal("5000.00")
    assert item.total_volume == Decimal("0.100")
    assert isinstance(item.id, type(uuid4()))


def test_order_item_custom_id():
    item_id = uuid4()
    item = OrderItem(
        order_id=uuid4(),
        product_id=uuid4(),
        quantity=5,
        price_at_order=Decimal("10000.00"),
        total_volume=Decimal("0.250"),
        id=item_id,
    )
    assert item.id == item_id
