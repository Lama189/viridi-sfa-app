import asyncio
from io import BytesIO
from urllib.parse import quote, unquote

from minio import Minio
from minio.error import S3Error

from app.application.interfaces.object_storage import IObjectStorage


class MinioStorage(IObjectStorage):
    def __init__(
        self,
        client: Minio,
    ) -> None:
        self._client = client

    def upload_sync(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> str:
        metadata = None

        if filename:
            metadata = {"X-Amz-Meta-Original-Name": quote(filename)}

        self._client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
            metadata=metadata,
        )

        return object_name

    async def upload(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self.upload_sync,
            bucket_name,
            object_name,
            data,
            content_type,
            filename,
        )

    def download_sync(
        self,
        bucket_name: str,
        object_name: str,
    ) -> tuple[bytes, str | None]:
        response = self._client.get_object(
            bucket_name,
            object_name,
        )

        try:
            file_bytes = response.read()

            headers = response.headers or {}

            raw_filename = headers.get("x-amz-meta-original-name")

            filename = unquote(raw_filename) if raw_filename else None

            return file_bytes, filename

        finally:
            response.close()
            response.release_conn()

    async def download(
        self,
        bucket_name: str,
        object_name: str,
    ) -> tuple[bytes, str | None]:
        return await asyncio.to_thread(
            self.download_sync,
            bucket_name,
            object_name,
        )

    def delete_sync(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        self._client.remove_object(
            bucket_name,
            object_name,
        )

    async def delete(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        await asyncio.to_thread(
            self.delete_sync,
            bucket_name,
            object_name,
        )

    def exists_sync(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bool:
        try:
            self._client.stat_object(
                bucket_name,
                object_name,
            )
            return True

        except S3Error:
            return False

    async def exists(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bool:
        return await asyncio.to_thread(
            self.exists_sync,
            bucket_name,
            object_name,
        )

    def get_url_sync(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        return self._client.presigned_get_object(
            bucket_name,
            object_name,
            expires=expires,
        )

    async def get_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        return await asyncio.to_thread(
            self.get_url_sync,
            bucket_name,
            object_name,
            expires,
        )
