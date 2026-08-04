from minio import Minio

from app.core.config import get_settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client

    if _client is None:
        settings = get_settings()

        _client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    return _client
