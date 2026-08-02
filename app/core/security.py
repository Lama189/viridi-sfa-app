import bcrypt
import hmac
import json
import jwt
import secrets
import hashlib
import urllib.parse
from jwt.exceptions import InvalidTokenError
from typing import Any
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from starlette import status
from cryptography.fernet import Fernet

from app.core.config import get_settings

settings = get_settings()


class SecurityUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        
        return hashed_bytes.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False

    @staticmethod
    def generate_access_token(data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def generate_refresh_token(data: dict[str, Any]) -> str:
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"}) 
        return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

    @staticmethod
    def verify_token(token: str, expected_type: str = "access") -> dict:
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            if payload.get("sub") is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token payload is invalid: missing subject",
                )
            if payload.get("type") != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type: expected {expected_type}",
                )
            return payload
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials or token expired",
            )
        
    @staticmethod
    def generate_invite_code() -> tuple[str, str, str]:
        raw_code = secrets.token_urlsafe(12)

        encrypted_code = SecurityUtils.encrypt_invite_code(raw_code)
        code_hash = SecurityUtils.hash_invite_code(raw_code)

        return raw_code, encrypted_code, code_hash
    
    @staticmethod
    def encrypt_invite_code(code: str) -> str:
        cipher = Fernet(settings.invite_code_secret_key.encode())
        encrypted = cipher.encrypt(code.encode())

        return encrypted.decode()
    
    @staticmethod
    def decrypt_invite_code(encrypted_code: str) -> str:
        cipher = Fernet(settings.invite_code_secret_key.encode())
        decrypted = cipher.decrypt(encrypted_code.encode())

        return decrypted.decode()
    
    @staticmethod
    def hash_invite_code(code: str) -> str:
        return hashlib.sha256(
            code.encode()
        ).hexdigest()

    @staticmethod
    def verify_telegram_init_data(init_data: str, bot_token: str) -> dict[str, Any]:
        if not bot_token:
            raise ValueError("Telegram bot token is not configured")

        parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        if "hash" not in parsed_data:
            raise ValueError("Invalid initData: missing hash")

        received_hash = parsed_data.pop("hash")

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed_data.items())
        )

        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash.lower(), received_hash.lower()):
            raise ValueError("Invalid initData: signature mismatch")

        if "user" in parsed_data:
            try:
                parsed_data["user"] = json.loads(parsed_data["user"])
            except Exception:
                pass

        return parsed_data