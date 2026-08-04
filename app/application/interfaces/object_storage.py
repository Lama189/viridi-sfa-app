from abc import ABC, abstractmethod


class IObjectStorage(ABC):
    @abstractmethod
    async def upload(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def download(
        self,
        bucket_name: str,
        object_name: str,
    ) -> tuple[bytes, str | None]:
        raise NotImplementedError

    @abstractmethod
    async def delete(
        self,
        bucket_name: str,
        object_name: str,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def exists(
        self,
        bucket_name: str,
        object_name: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        raise NotImplementedError
