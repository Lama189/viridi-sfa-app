from uuid import uuid4

from app.domain.entities.users import User
from app.domain.enums import EmployeeRole


def test_user_default_values():
    u = User(phone="+998901234567", full_name="Test User")
    assert u.phone == "+998901234567"
    assert u.full_name == "Test User"
    assert u.password_hash is None
    assert isinstance(u.id, type(uuid4()))
    assert u.role == EmployeeRole.AGENT
    assert u.telegram_chat_id is None
    assert u.is_active is True


def test_user_custom_values():
    uid = uuid4()
    u = User(
        phone="+998909999999",
        full_name="Admin User",
        password_hash="hashed",
        id=uid,
        role=EmployeeRole.ADMIN,
        telegram_chat_id=999999,
        is_active=False,
    )
    assert u.id == uid
    assert u.password_hash == "hashed"
    assert u.role == EmployeeRole.ADMIN
    assert u.telegram_chat_id == 999999
    assert u.is_active is False


def test_user_is_active_toggle():
    u = User(phone="+998901234567", full_name="X")
    u.is_active = False
    assert u.is_active is False
    u.is_active = True
    assert u.is_active is True
