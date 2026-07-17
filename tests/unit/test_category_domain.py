from uuid import uuid4

from app.domain.entities.inventory import Category


def test_category_default_values():
    c = Category(name="Fertilizers")
    assert c.name == "Fertilizers"
    assert isinstance(c.id, type(uuid4()))
    assert c.is_active is True


def test_category_custom_values():
    uid = uuid4()
    c = Category(name="Seeds", id=uid, is_active=False)
    assert c.id == uid
    assert c.name == "Seeds"
    assert c.is_active is False


def test_category_is_active_toggle():
    c = Category(name="Tools", is_active=True)
    c.is_active = False
    assert c.is_active is False
