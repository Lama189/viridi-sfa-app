from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.invite_codes import ClientInviteCode


class IInviteCodeRepository(ABC):

    @abstractmethod
    async def add(self, invite_code: ClientInviteCode) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_many(self, invite_codes: list[ClientInviteCode]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, invite_code_id: UUID) -> ClientInviteCode | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_retail_point(self, retail_point_id: UUID) -> ClientInviteCode | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_code_hash(self, code_hash: str) -> ClientInviteCode | None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, retail_point_id: UUID, code_hash: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def update(self, invite_code: ClientInviteCode) -> None:
        raise NotImplementedError
