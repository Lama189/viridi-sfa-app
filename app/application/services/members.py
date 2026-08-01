from uuid import UUID

from app.application.interfaces.uow import IUnitOfWork
from app.application.interfaces.services.invite_codes import IClientInviteCodesService
from app.application.interfaces.services.retail_point_members import IRetailPointMembersService
from app.domain.entities.retail_point_members import RetailPointMember
from app.core.extensions import (
    UserNotFoundError,
    UserNotActiveError,
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
    RetailPointNotFoundError,
    RetailPointInactiveError,
)
from app.core.observability.metrics import retail_point_member_operations_total


class RetailPointMembersService(IRetailPointMembersService):
    
    def __init__(
        self, 
        uow: IUnitOfWork,
        invite_codes: IClientInviteCodesService
    ) -> None:
        self._uow = uow
        self._invite_codes = invite_codes

    async def _validate_retail_point(
        self,
        retail_point_id: UUID,
    ) -> None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if retail_point is None:
            raise RetailPointNotFoundError()

        if not retail_point.is_active:
            raise RetailPointInactiveError()
        
    async def _validate_client(
        self,
        client_id: UUID,
    ) -> None:
        client = await self._uow.clients.get_by_id(client_id)
        if client is None:
            raise UserNotFoundError()
        
        if not client.is_active:
            raise UserNotActiveError()

    async def join(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> RetailPointMember:
        await self._validate_client(client_id)
        await self._validate_retail_point(retail_point_id)

        exists = await self._uow.retail_point_members.exists(retail_point_id, client_id)
        if exists:
            raise MembershipAlreadyExistsError()
        
        membership = RetailPointMember(
            retail_point_id,
            client_id
        )

        await self._uow.retail_point_members.add(membership)
        retail_point_member_operations_total.labels(action="join").inc()

        return membership
    
    async def leave(
        self, 
        retail_point_id: UUID,
        client_id: UUID
    ) -> RetailPointMember:
        membership = await self._uow.retail_point_members.get_by_retail_point_and_client(
            retail_point_id,
            client_id
        )
        if not membership:
            raise MembershipNotFoundError()
        
        await self._uow.retail_point_members.delete(membership)
        retail_point_member_operations_total.labels(action="leave").inc()

        return membership
    
    async def remove(
        self, 
        retail_point_id: UUID,
        client_id: UUID
    ) -> RetailPointMember:
        membership = await self._uow.retail_point_members.get_by_retail_point_and_client(
            retail_point_id,
            client_id
        )
        if not membership:
            raise MembershipNotFoundError()
        
        await self._uow.retail_point_members.delete(membership)
        retail_point_member_operations_total.labels(action="remove").inc()

        return membership
    
    async def get_member(
        self, 
        retail_point_id: UUID,
        client_id: UUID
    ) -> RetailPointMember:
        membership = await self._uow.retail_point_members.get_by_retail_point_and_client(
            retail_point_id,
            client_id
        )
        if not membership:
            raise MembershipNotFoundError()

        return membership

    async def list_members(
        self,
        retail_point_id: UUID,
    ) -> list[RetailPointMember]:
        await self._validate_retail_point(retail_point_id)

        return await self._uow.retail_point_members.get_by_retail_point(retail_point_id)
    
    async def is_member(
        self,
        retail_point_id: UUID,
        client_id: UUID,
    ) -> bool:
        return await self._uow.retail_point_members.exists(
            retail_point_id,
            client_id,
        )

    async def get_by_telegram(
        self,
        telegram_id: int,
    ) -> RetailPointMember:
        membership = await self._uow.retail_point_members.get_by_telegram_id(telegram_id)
        if not membership:
            raise MembershipNotFoundError()
        
        return membership
