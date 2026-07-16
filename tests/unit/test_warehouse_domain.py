from uuid import uuid4

from app.domain.entities.inventory import Warehouse


def test_warehouse_default_values():
    w = Warehouse(name="Test")
    assert w.name == "Test"
    assert isinstance(w.id, type(uuid4()))
    assert w.address is None
    assert w.is_active is True


def test_warehouse_custom_values():
    uid = uuid4()
    w = Warehouse(name="Main", id=uid, address="ul. Lenina 1", is_active=False)
    assert w.id == uid
    assert w.address == "ul. Lenina 1"
    assert w.is_active is False


def test_warehouse_address_optional():
    w = Warehouse(name="NoAddr")
    assert w.address is None


def test_warehouse_is_active_toggle():
    w = Warehouse(name="W", is_active=True)
    w.is_active = False
    assert w.is_active is False
