from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.clients import Client


class IClientRepository(ABC):
    @abstractmethod
    async def add(self, client: Client) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, client_id: UUID) -> Client | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_phone(self, phone: str) -> Client | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_telegram_chat_id(self, telegram_chat_id: int) -> Client | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, only_active: bool = True) -> list[Client]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, client: Client) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, client: Client) -> None:
        raise NotImplementedError
