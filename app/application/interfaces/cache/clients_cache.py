from abc import ABC, abstractmethod

from app.domain.entities.auth import AuthenticatedClient


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
        user: AuthenticatedClient,
        expire_seconds: int = 900,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_user(self, client_id: str) -> AuthenticatedClient | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, client_id: str) -> None:
        raise NotImplementedError
