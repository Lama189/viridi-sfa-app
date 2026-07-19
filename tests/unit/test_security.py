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
