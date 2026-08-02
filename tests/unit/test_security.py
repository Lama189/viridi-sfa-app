from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from app.core.security import SecurityUtils


# --- hash_password / verify_password ---

def test_hash_and_verify_password():
    hashed = SecurityUtils.hash_password("my_secret")
    assert SecurityUtils.verify_password("my_secret", hashed) is True


def test_verify_wrong_password():
    hashed = SecurityUtils.hash_password("my_secret")
    assert SecurityUtils.verify_password("wrong_password", hashed) is False


def test_verify_password_exception_returns_false():
    assert SecurityUtils.verify_password("any", "!!!invalid!!!") is False


# --- generate_access_token / generate_refresh_token ---

@patch("app.core.security.get_settings")
def test_generate_access_token(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    token = SecurityUtils.generate_access_token({"sub": "user-123"})
    assert isinstance(token, str)
    assert len(token) > 0


@patch("app.core.security.get_settings")
def test_generate_refresh_token(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        refresh_token_expire_days=30,
    )
    token = SecurityUtils.generate_refresh_token({"sub": "user-123"})
    assert isinstance(token, str)
    assert len(token) > 0


# --- verify_token ---

@patch("app.core.security.get_settings")
def test_verify_token_success(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    token = SecurityUtils.generate_access_token({"sub": "user-123"})
    payload = SecurityUtils.verify_token(token, expected_type="access")

    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


@patch("app.core.security.get_settings")
def test_verify_token_missing_sub(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    import jwt as _jwt
    now = datetime.now(timezone.utc)
    token = _jwt.encode(
        {"exp": now + timedelta(minutes=15), "type": "access"},
        "test-secret",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        SecurityUtils.verify_token(token, expected_type="access")
    assert exc_info.value.status_code == 401


@patch("app.core.security.get_settings")
def test_verify_token_wrong_type(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    token = SecurityUtils.generate_access_token({"sub": "user-123"})

    with pytest.raises(HTTPException) as exc_info:
        SecurityUtils.verify_token(token, expected_type="refresh")
    assert exc_info.value.status_code == 401
    assert "Invalid token type" in exc_info.value.detail


@patch("app.core.security.get_settings")
def test_verify_token_expired(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    import jwt
    now = datetime.now(timezone.utc)
    expired_token = jwt.encode(
        {"sub": "user-123", "type": "access", "exp": now - timedelta(hours=1)},
        "test-secret",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        SecurityUtils.verify_token(expired_token, expected_type="access")
    assert exc_info.value.status_code == 401


@patch("app.core.security.get_settings")
def test_verify_token_invalid_signature(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        access_token_expire_minutes=15,
    )
    import jwt
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": "user-123", "type": "access", "exp": now + timedelta(minutes=15)},
        "wrong-secret",
        algorithm="HS256",
    )

    with pytest.raises(HTTPException) as exc_info:
        SecurityUtils.verify_token(token, expected_type="access")
    assert exc_info.value.status_code == 401


# --- refresh token roundtrip ---

@patch("app.core.security.get_settings")
def test_refresh_token_roundtrip(mock_settings):
    mock_settings.return_value = MagicMock(
        secret_key="test-secret",
        algorithm="HS256",
        refresh_token_expire_days=30,
    )
    token = SecurityUtils.generate_refresh_token({"sub": "user-456"})
    payload = SecurityUtils.verify_token(token, expected_type="refresh")

    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"


# --- verify_telegram_init_data ---

def test_verify_telegram_init_data_success():
    import hmac
    import hashlib
    import json
    import urllib.parse

    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    user_obj = {"id": 123456789, "first_name": "TestUser"}
    data_dict = {
        "auth_date": "1600000000",
        "query_id": "AA...",
        "user": json.dumps(user_obj),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    data_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    init_data = urllib.parse.urlencode(data_dict) + f"&hash={data_hash}"

    parsed = SecurityUtils.verify_telegram_init_data(init_data, bot_token)
    assert parsed["user"]["id"] == 123456789
    assert parsed["auth_date"] == "1600000000"


def test_verify_telegram_init_data_invalid_hash():
    import urllib.parse

    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    data_dict = {"auth_date": "1600000000", "user": '{"id": 123456789}'}
    init_data = urllib.parse.urlencode(data_dict) + "&hash=badhash"

    with pytest.raises(ValueError, match="signature mismatch"):
        SecurityUtils.verify_telegram_init_data(init_data, bot_token)


def test_verify_telegram_init_data_missing_hash():
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    init_data = "auth_date=1600000000"

    with pytest.raises(ValueError, match="missing hash"):
        SecurityUtils.verify_telegram_init_data(init_data, bot_token)


def test_verify_telegram_init_data_empty_bot_token():
    with pytest.raises(ValueError, match="bot token is not configured"):
        SecurityUtils.verify_telegram_init_data("auth_date=1600000000&hash=123", "")

