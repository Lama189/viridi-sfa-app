from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.retail_point_members import RetailPointMember


class IRetailPointMembersService(ABC):
    @abstractmethod
    async def join(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> RetailPointMember:
        raise NotImplementedError

    @abstractmethod
    async def leave(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> RetailPointMember:
        raise NotImplementedError

    @abstractmethod
    async def remove(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> RetailPointMember:
        raise NotImplementedError

    @abstractmethod
    async def get_member(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> RetailPointMember:
        raise NotImplementedError

    @abstractmethod
    async def list_members(
        self,
        retail_point_id: UUID,
    ) -> list[RetailPointMember]:
        raise NotImplementedError

    @abstractmethod
    async def is_member(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_telegram(
        self,
        telegram_id: int,
    ) -> RetailPointMember:
        raise NotImplementedError
