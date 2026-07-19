from uuid import uuid4

from app.domain.entities.clients import Client


def test_client_default_values():
    c = Client(phone="+998901234567", full_name="Test Client")
    assert c.phone == "+998901234567"
    assert c.full_name == "Test Client"
    assert c.password_hash is None
    assert isinstance(c.id, type(uuid4()))
    assert c.telegram_chat_id is None
    assert c.is_active is True


def test_client_custom_values():
    uid = uuid4()
    c = Client(
        phone="+998909999999",
        full_name="Custom Client",
        password_hash="hashed",
        id=uid,
        telegram_chat_id=123456789,
        is_active=False,
    )
    assert c.id == uid
    assert c.password_hash == "hashed"
    assert c.telegram_chat_id == 123456789
    assert c.is_active is False


def test_client_is_active_toggle():
    c = Client(phone="+998901234567", full_name="X")
    c.is_active = False
    assert c.is_active is False
    c.is_active = True
    assert c.is_active is True


def test_client_password_hash_optional():
    c = Client(phone="+998901234567", full_name="No Pass")
    assert c.password_hash is None


def test_client_telegram_chat_id_optional():
    c = Client(phone="+998901234567", full_name="No TG")
    assert c.telegram_chat_id is None
