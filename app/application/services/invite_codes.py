from uuid import UUID

from app.application.interfaces.services.invite_codes import IClientInviteCodesService
from app.application.interfaces.uow import IUnitOfWork
from app.core.extensions import (
    InvalidInviteCodeError,
    UserNotActiveError,
    UserNotFoundError,
)
from app.core.security import SecurityUtils
from app.domain.entities.invite_codes import ClientInviteCode


class ClientInviteCodesService(IClientInviteCodesService):

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def _validate_retail_point(
        self,
        retail_point_id: UUID,
    ) -> None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)

        if retail_point is None:
            raise ValueError(f"Retail Point with ID {retail_point_id} not found")

        if not retail_point.is_active:
            raise ValueError("Retail Point is inactive")

    async def _validate_employee(
        self,
        employee_id: UUID,
    ) -> None:
        employee = await self._uow.employees.get_by_id(employee_id)

        if employee is None:
            raise UserNotFoundError()

        if not employee.is_active:
            raise UserNotActiveError()

    async def create(
        self,
        employee_id: UUID,
        retail_point_id: UUID,
    ) -> str:
        await self._validate_retail_point(retail_point_id)

        raw_code, encrypted_code, code_hash = SecurityUtils.generate_invite_code()

        invite_code = ClientInviteCode.create(
            retail_point_id=retail_point_id,
            created_by_employee_id=employee_id,
            encrypted_code=encrypted_code,
            code_hash=code_hash,
        )

        await self._uow.invite_codes.add(invite_code)

        return raw_code

    async def regenerate(
        self,
        employee_id: UUID,
        retail_point_id: UUID,
    ) -> str:
        await self._validate_employee(employee_id)
        await self._validate_retail_point(retail_point_id)

        invite_code = await self._uow.invite_codes.get_by_retail_point(retail_point_id)

        if invite_code is None:
            raise ValueError(
                f"There is no invite code for retail point with ID {retail_point_id}"
            )

        raw_code, encrypted_code, code_hash = SecurityUtils.generate_invite_code()

        invite_code.regenerate(
            encrypted_code=encrypted_code,
            code_hash=code_hash,
        )

        await self._uow.invite_codes.update(invite_code)
        await self._uow.commit()

        return raw_code

    async def activate(
        self,
        raw_code: str,
        client_id: UUID,
    ) -> ClientInviteCode:
        invite_code = await self._uow.invite_codes.get_by_code_hash(
            SecurityUtils.hash_invite_code(raw_code)
        )

        if invite_code is None:
            raise InvalidInviteCodeError("Invite code not found")

        try:
            invite_code.activate(client_id)
        except ValueError:
            raise InvalidInviteCodeError("Invite code is invalid or expired")

        await self._uow.invite_codes.update(invite_code)
        await self._uow.commit()

        return invite_code

    async def deactivate(
        self,
        invite_code_id: UUID,
    ) -> ClientInviteCode:
        invite_code = await self._uow.invite_codes.get_by_id(invite_code_id)

        if invite_code is None:
            raise InvalidInviteCodeError("Invite code not found")

        invite_code.deactivate()

        await self._uow.invite_codes.update(invite_code)
        await self._uow.commit()

        return invite_code

    async def get(
        self,
        invite_code_id: UUID,
    ) -> ClientInviteCode:
        invite_code = await self._uow.invite_codes.get_by_id(invite_code_id)

        if invite_code is None:
            raise InvalidInviteCodeError("Invite code not found")

        return invite_code

    async def get_by_retail_point(
        self,
        retail_point_id: UUID,
    ) -> ClientInviteCode:
        invite_code = await self._uow.invite_codes.get_by_retail_point(retail_point_id)

        if invite_code is None:
            raise InvalidInviteCodeError("Invite code not found")

        return invite_code

    async def get_raw_code(
        self,
        retail_point_id: UUID,
    ) -> str:
        invite_code = await self.get_by_retail_point(retail_point_id)

        return SecurityUtils.decrypt_invite_code(
            invite_code.encrypted_code
        )