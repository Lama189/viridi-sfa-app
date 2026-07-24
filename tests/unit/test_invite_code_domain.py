from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest

from app.domain.entities.invite_codes import ClientInviteCode


def _make_code(**overrides):
    defaults = dict(
        retail_point_id=uuid4(),
        encrypted_code="enc",
        code_hash="hash",
        created_by_employee_id=uuid4(),
    )
    defaults.update(overrides)
    return ClientInviteCode(**defaults)


def test_invite_code_default_values():
    code = _make_code()
    assert isinstance(code.id, type(uuid4()))
    assert code.is_active is True
    assert code.last_activated_client_id is None
    assert code.last_activated_at is None
    assert code.expires_at is None
    assert code.created_at is not None
    assert code.updated_at is not None


def test_invite_code_create_classmethod():
    rp_id = uuid4()
    emp_id = uuid4()
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    code = ClientInviteCode.create(
        retail_point_id=rp_id,
        encrypted_code="enc",
        code_hash="hash",
        created_by_employee_id=emp_id,
        expires_in=timedelta(hours=24),
        now=now,
    )
    assert code.retail_point_id == rp_id
    assert code.created_by_employee_id == emp_id
    assert code.expires_at == now + timedelta(hours=24)
    assert code.created_at == now
    assert code.updated_at == now


def test_invite_code_create_no_expiry():
    code = ClientInviteCode.create(
        retail_point_id=uuid4(),
        encrypted_code="enc",
        code_hash="hash",
        created_by_employee_id=uuid4(),
    )
    assert code.expires_at is None


def test_invite_code_activate():
    now = datetime(2025, 6, 1, tzinfo=timezone.utc)
    code = _make_code()
    client_id = uuid4()

    code.activate(client_id, now=now)

    assert code.last_activated_client_id == client_id
    assert code.last_activated_at == now
    assert code.updated_at == now


def test_invite_code_activate_expired_raises():
    past = datetime(2025, 1, 1, tzinfo=timezone.utc)
    code = _make_code()
    code.expires_at = past

    with pytest.raises(ValueError, match="not available"):
        code.activate(uuid4(), now=datetime(2025, 6, 1, tzinfo=timezone.utc))


def test_invite_code_activate_inactive_raises():
    code = _make_code()
    code.is_active = False

    with pytest.raises(ValueError, match="not available"):
        code.activate(uuid4())


def test_invite_code_regenerate():
    now = datetime(2025, 6, 1, tzinfo=timezone.utc)
    code = _make_code()
    code.is_active = False
    code.last_activated_client_id = uuid4()

    code.regenerate(encrypted_code="new_enc", code_hash="new_hash", now=now)

    assert code.encrypted_code == "new_enc"
    assert code.code_hash == "new_hash"
    assert code.is_active is True
    assert code.last_activated_client_id is None
    assert code.last_activated_at is None
    assert code.updated_at == now


def test_invite_code_deactivate():
    now = datetime(2025, 6, 1, tzinfo=timezone.utc)
    code = _make_code()

    code.deactivate(now=now)

    assert code.is_active is False
    assert code.updated_at == now


def test_invite_code_is_available_active_no_expiry():
    code = _make_code()
    assert code.is_available() is True


def test_invite_code_is_available_inactive():
    code = _make_code()
    code.is_active = False
    assert code.is_available() is False


def test_invite_code_is_available_expired():
    code = _make_code()
    code.expires_at = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert code.is_available(now=datetime(2025, 6, 1, tzinfo=timezone.utc)) is False


def test_invite_code_is_available_not_yet_expired():
    code = _make_code()
    code.expires_at = datetime(2030, 1, 1, tzinfo=timezone.utc)
    assert code.is_available(now=datetime(2025, 6, 1, tzinfo=timezone.utc)) is True


def test_invite_code_change_expiration():
    now = datetime(2025, 6, 1, tzinfo=timezone.utc)
    code = _make_code()

    new_exp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    code.change_expiration(new_exp, now=now)

    assert code.expires_at == new_exp
    assert code.updated_at == now


def test_invite_code_change_expiration_to_none():
    code = _make_code()
    code.expires_at = datetime(2030, 1, 1, tzinfo=timezone.utc)

    code.change_expiration(None)

    assert code.expires_at is None
