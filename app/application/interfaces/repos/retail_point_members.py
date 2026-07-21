from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.retail_point_members import RetailPointMember


class IRetailPointMemberRepository(ABC):

    @abstractmethod
    async def add(self, member: RetailPointMember) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, member_id: UUID) -> RetailPointMember | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> RetailPointMember | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_retail_point(self, retail_point_id: UUID) -> list[RetailPointMember]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_retail_point_and_client(
        self, retail_point_id: UUID, client_id: UUID,
    ) -> RetailPointMember | None:
        raise NotImplementedError

    @abstractmethod
    async def exists(self, retail_point_id: UUID, client_id: UUID) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def update(self, member: RetailPointMember) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, member: RetailPointMember) -> None:
        raise NotImplementedError
