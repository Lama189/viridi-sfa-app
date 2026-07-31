from decimal import Decimal
from uuid import uuid4

from app.domain.entities.inventory import Product


def test_product_default_values():
    uid = uuid4()
    p = Product(category_id=uid, name="NPK-10", price=Decimal("150.00"))
    assert p.name == "NPK-10"
    assert p.category_id == uid
    assert p.price == Decimal("150.00")
    assert isinstance(p.id, type(uuid4()))
    assert p.volume == Decimal("0.000")
    assert p.weight == Decimal("0.000")
    assert p.items_in_box == 1
    assert p.is_active is True


def test_product_custom_values():
    cat_uid = uuid4()
    prod_uid = uuid4()
    p = Product(
        category_id=cat_uid,
        name="Urea",
        price=Decimal("89000.00"),
        id=prod_uid,
        volume=Decimal("0.050"),
        weight=Decimal("25.000"),
        items_in_box=40,
        is_active=False,
    )
    assert p.id == prod_uid
    assert p.volume == Decimal("0.050")
    assert p.weight == Decimal("25.000")
    assert p.items_in_box == 40
    assert p.is_active is False


def test_product_is_active_toggle():
    p = Product(category_id=uuid4(), name="X", price=Decimal("10.00"))
    p.is_active = False
    assert p.is_active is False
