from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.users import User


class IUserRepository(ABC):

    @abstractmethod
    async def add(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_phone(self, phone: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, only_active: bool = True) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, user: User) -> None:
        raise NotImplementedError
