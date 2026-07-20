from abc import ABC, abstractmethod

from app.api.v1.schemas.clients import ClientCachedDTO


class IClientsCacheRepository(ABC):

    @abstractmethod
    async def get_refresh_token(self, client_id: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def set_refresh_token(
        self,
        client_id: str,
        token: str,
        expire_days: int = 30,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_refresh_token(self, client_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def set_user(
        self,
        client_id: str,
        user: ClientCachedDTO,
        expire_seconds: int = 900,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_user(self, client_id: str) -> ClientCachedDTO | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, client_id: str) -> None:
        raise NotImplementedError
