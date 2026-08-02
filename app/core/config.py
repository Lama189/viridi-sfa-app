from pydantic_settings import BaseSettings, SettingsConfigDict

from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = ""
    redis_url: str = ""
    secret_key: str = ""
    invite_code_secret_key: str = ""
    telegram_bot_token: str = ""

    debug: bool = False
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_secure: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()