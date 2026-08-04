from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.entities.orders import Order, OrderItem
from app.domain.enums import OrderStatus

# ---------------------------------------------------------------------------
# OrderItem
# ---------------------------------------------------------------------------


class TestOrderItem:
    def test_create_basic(self):
        item = OrderItem(
            order_id=uuid4(),
            product_id=uuid4(),
            quantity=10,
            price_at_order=Decimal("5000.00"),
            total_volume=Decimal("0.100"),
        )
        assert isinstance(item.id, type(uuid4()))
        assert item.quantity == 10
        assert item.price_at_order == Decimal("5000.00")
        assert item.total_volume == Decimal("0.100")

    def test_custom_id(self):
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

    def test_total_price_property(self):
        item = OrderItem(
            order_id=uuid4(),
            product_id=uuid4(),
            quantity=7,
            price_at_order=Decimal("3000.00"),
            total_volume=Decimal("0.070"),
        )
        assert item.total_price == Decimal("21000.00")

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError, match="positive"):
            OrderItem(
                order_id=uuid4(),
                product_id=uuid4(),
                quantity=0,
                price_at_order=Decimal("100.00"),
                total_volume=Decimal("0.010"),
            )

    def test_negative_quantity_raises(self):
        with pytest.raises(ValueError, match="positive"):
            OrderItem(
                order_id=uuid4(),
                product_id=uuid4(),
                quantity=-1,
                price_at_order=Decimal("100.00"),
                total_volume=Decimal("0.010"),
            )

    def test_negative_price_raises(self):
        with pytest.raises(ValueError, match="negative"):
            OrderItem(
                order_id=uuid4(),
                product_id=uuid4(),
                quantity=1,
                price_at_order=Decimal("-1.00"),
                total_volume=Decimal("0.001"),
            )

    def test_zero_price_allowed(self):
        item = OrderItem(
            order_id=uuid4(),
            product_id=uuid4(),
            quantity=1,
            price_at_order=Decimal("0.00"),
            total_volume=Decimal("0.001"),
        )
        assert item.price_at_order == Decimal("0.00")

    def test_negative_volume_raises(self):
        with pytest.raises(ValueError, match="negative"):
            OrderItem(
                order_id=uuid4(),
                product_id=uuid4(),
                quantity=1,
                price_at_order=Decimal("100.00"),
                total_volume=Decimal("-0.010"),
            )


# ---------------------------------------------------------------------------
# Order — defaults & basic properties
# ---------------------------------------------------------------------------


class TestOrderDefaults:
    def test_default_values(self):
        order = Order(
            warehouse_id=uuid4(), created_by_id=uuid4(), retail_point_id=uuid4()
        )
        assert isinstance(order.id, type(uuid4()))
        assert order.visit_id is None
        assert order.status == OrderStatus.PENDING
        assert order.total_amount == Decimal("0.00")
        assert order.total_volume == Decimal("0.000")
        assert order.items == []

    def test_custom_values(self):
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

    def test_negative_total_amount_raises(self):
        with pytest.raises(ValueError, match="negative"):
            Order(
                warehouse_id=uuid4(),
                created_by_id=uuid4(),
                retail_point_id=uuid4(),
                total_amount=Decimal("-100.00"),
            )

    def test_negative_total_volume_raises(self):
        with pytest.raises(ValueError, match="negative"):
            Order(
                warehouse_id=uuid4(),
                created_by_id=uuid4(),
                retail_point_id=uuid4(),
                total_volume=Decimal("-1.000"),
            )


# ---------------------------------------------------------------------------
# Order — add_item / remove_item / clear_items
# ---------------------------------------------------------------------------


class TestOrderItemManipulation:
    def _make_order(self, **kwargs):
        defaults = {
            "warehouse_id": uuid4(),
            "created_by_id": uuid4(),
            "retail_point_id": uuid4(),
        }
        defaults.update(kwargs)
        return Order(**defaults)

    def _make_item(
        self,
        order_id,
        product_id=None,
        quantity=10,
        price=Decimal("5000.00"),
        volume=Decimal("0.100"),
    ):
        return OrderItem(
            order_id=order_id,
            product_id=product_id or uuid4(),
            quantity=quantity,
            price_at_order=price,
            total_volume=volume,
        )

    def test_add_item_updates_totals(self):
        order = self._make_order()
        item = self._make_item(
            order.id, quantity=5, price=Decimal("2000.00"), volume=Decimal("0.050")
        )
        order.add_item(item)

        assert len(order.items) == 1
        assert order.total_amount == Decimal("10000.00")
        assert order.total_volume == Decimal("0.050")

    def test_add_multiple_items(self):
        order = self._make_order()
        i1 = self._make_item(
            order.id, quantity=2, price=Decimal("1000.00"), volume=Decimal("0.020")
        )
        i2 = self._make_item(
            order.id, quantity=3, price=Decimal("500.00"), volume=Decimal("0.030")
        )
        order.add_item(i1)
        order.add_item(i2)

        assert len(order.items) == 2
        assert order.total_amount == Decimal("3500.00")
        assert order.total_volume == Decimal("0.050")

    def test_add_item_wrong_order_id_raises(self):
        order = self._make_order()
        item = OrderItem(
            order_id=uuid4(),
            product_id=uuid4(),
            quantity=1,
            price_at_order=Decimal("100.00"),
            total_volume=Decimal("0.010"),
        )
        with pytest.raises(ValueError, match="another order"):
            order.add_item(item)

    def test_remove_item_updates_totals(self):
        order = self._make_order()
        pid = uuid4()
        item = self._make_item(
            order.id,
            product_id=pid,
            quantity=5,
            price=Decimal("2000.00"),
            volume=Decimal("0.050"),
        )
        order.add_item(item)
        order.remove_item(pid)

        assert len(order.items) == 0
        assert order.total_amount == Decimal("0.00")
        assert order.total_volume == Decimal("0.000")

    def test_remove_item_not_found_raises(self):
        order = self._make_order()
        with pytest.raises(ValueError, match="not found"):
            order.remove_item(uuid4())

    def test_clear_items(self):
        order = self._make_order()
        order.add_item(
            self._make_item(
                order.id, quantity=2, price=Decimal("1000.00"), volume=Decimal("0.020")
            )
        )
        order.add_item(
            self._make_item(
                order.id, quantity=3, price=Decimal("500.00"), volume=Decimal("0.030")
            )
        )
        order.clear_items()

        assert order.items == []
        assert order.total_amount == Decimal("0.00")
        assert order.total_volume == Decimal("0.000")


# ---------------------------------------------------------------------------
# Order — lifecycle (confirm / ship / cancel / recalculate)
# ---------------------------------------------------------------------------


class TestOrderLifecycle:
    def _make_order_with_item(self):
        order = Order(
            warehouse_id=uuid4(), created_by_id=uuid4(), retail_point_id=uuid4()
        )
        item = OrderItem(
            order_id=order.id,
            product_id=uuid4(),
            quantity=10,
            price_at_order=Decimal("5000.00"),
            total_volume=Decimal("0.100"),
        )
        order.add_item(item)
        return order

    def test_confirm_pending(self):
        order = self._make_order_with_item()
        order.confirm()
        assert order.status == OrderStatus.CONFIRMED

    def test_confirm_without_items_raises(self):
        order = Order(
            warehouse_id=uuid4(), created_by_id=uuid4(), retail_point_id=uuid4()
        )
        with pytest.raises(ValueError, match="at least one item"):
            order.confirm()

    def test_confirm_non_pending_raises(self):
        order = self._make_order_with_item()
        order.confirm()
        with pytest.raises(ValueError, match="pending"):
            order.confirm()

    def test_ship_confirmed(self):
        order = self._make_order_with_item()
        order.confirm()
        order.ship()
        assert order.status == OrderStatus.SHIPPED

    def test_ship_non_confirmed_raises(self):
        order = self._make_order_with_item()
        with pytest.raises(ValueError, match="confirmed"):
            order.ship()

    def test_cancel_pending(self):
        order = self._make_order_with_item()
        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_confirmed(self):
        order = self._make_order_with_item()
        order.confirm()
        order.cancel()
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_shipped_raises(self):
        order = self._make_order_with_item()
        order.confirm()
        order.ship()
        with pytest.raises(ValueError, match="Shipped"):
            order.cancel()

    def test_cancel_already_cancelled_raises(self):
        order = self._make_order_with_item()
        order.cancel()
        with pytest.raises(ValueError, match="already cancelled"):
            order.cancel()

    def test_recalculate(self):
        order = Order(
            warehouse_id=uuid4(),
            created_by_id=uuid4(),
            retail_point_id=uuid4(),
            total_amount=Decimal("999.99"),
            total_volume=Decimal("9.999"),
        )
        i1 = OrderItem(
            order_id=order.id,
            product_id=uuid4(),
            quantity=3,
            price_at_order=Decimal("1000.00"),
            total_volume=Decimal("0.030"),
        )
        i2 = OrderItem(
            order_id=order.id,
            product_id=uuid4(),
            quantity=2,
            price_at_order=Decimal("500.00"),
            total_volume=Decimal("0.020"),
        )
        order.items = [i1, i2]
        order.recalculate()

        assert order.total_amount == Decimal("4000.00")
        assert order.total_volume == Decimal("0.050")

    def test_touch_updates_updated_at(self):
        order = self._make_order_with_item()
        old = order.updated_at
        order.confirm()
        assert order.updated_at >= old
