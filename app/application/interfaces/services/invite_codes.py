from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.invite_codes import ClientInviteCode


class IClientInviteCodesService(ABC):
    @abstractmethod
    async def create(
        self,
        employee_id: UUID,
        retail_point_id: UUID,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def create_many(
        self, employee_id: UUID, retail_point_ids: list[UUID]
    ) -> dict[UUID, str]:
        raise NotImplementedError

    @abstractmethod
    async def regenerate(
        self,
        employee_id: UUID,
        retail_point_id: UUID,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def activate(
        self,
        raw_code: str,
        client_id: UUID,
    ) -> ClientInviteCode:
        raise NotImplementedError

    @abstractmethod
    async def deactivate(
        self,
        invite_code_id: UUID,
    ) -> ClientInviteCode:
        raise NotImplementedError

    @abstractmethod
    async def get(
        self,
        invite_code_id: UUID,
    ) -> ClientInviteCode:
        raise NotImplementedError

    @abstractmethod
    async def get_by_retail_point(
        self,
        retail_point_id: UUID,
    ) -> ClientInviteCode:
        raise NotImplementedError

    @abstractmethod
    async def get_raw_code(
        self,
        retail_point_id: UUID,
    ) -> str:
        raise NotImplementedError
