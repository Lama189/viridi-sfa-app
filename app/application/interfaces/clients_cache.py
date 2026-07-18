from abc import ABC, abstractmethod
from uuid import UUID

from app.api.v1.schemas.users import UserCachedDTO


class IClientsCacheRepository(ABC):

    @abstractmethod
    async def get_refresh_token(self, client_id: UUID) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def set_refresh_token(
        self,
        client_id: UUID,
        token: str,
        expire_days: int = 30,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete_refresh_token(self, client_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def set_user(
        self,
        client_id: UUID,
        user: UserCachedDTO,
        expire_seconds: int = 900,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_user(self, client_id: UUID) -> UserCachedDTO | None:
        raise NotImplementedError

    @abstractmethod
    async def delete_user(self, client_id: UUID) -> None:
        raise NotImplementedError
