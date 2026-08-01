from uuid import UUID

from app.core.observability.logging import logger
from app.core.observability.metrics import invite_code_operations_total
from app.application.interfaces.services.invite_codes import IClientInviteCodesService
from app.application.interfaces.uow import IUnitOfWork
from app.core.extensions import (
    InvalidInviteCodeError,
    UserNotActiveError,
    UserNotFoundError,
    RetailPointNotFoundError,
    RetailPointInactiveError,
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
            logger.warning(
                "Retail point not found during invite code validation",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointNotFoundError()

        if not retail_point.is_active:
            logger.warning(
                "Retail point is inactive during invite code validation",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointInactiveError()

    async def _validate_employee(
        self,
        employee_id: UUID,
    ) -> None:
        employee = await self._uow.employees.get_by_id(employee_id)

        if employee is None:
            logger.warning("Employee not found during invite code validation")
            raise UserNotFoundError()

        if not employee.is_active:
            logger.warning("Employee is inactive during invite code validation")
            raise UserNotActiveError()

    async def create(
        self,
        employee_id: UUID,
        retail_point_id: UUID,
    ) -> str:
        logger.info(
            "Creating invite code",
            retail_point_id=str(retail_point_id),
        )

        await self._validate_retail_point(retail_point_id)

        raw_code, encrypted_code, code_hash = SecurityUtils.generate_invite_code()

        invite_code = ClientInviteCode.create(
            retail_point_id=retail_point_id,
            created_by_employee_id=employee_id,
            encrypted_code=encrypted_code,
            code_hash=code_hash,
        )

        await self._uow.invite_codes.add(invite_code)

        logger.info(
            "Invite code successfully created",
            retail_point_id=str(retail_point_id),
        )
        invite_code_operations_total.labels(action="create").inc()

        return raw_code

    async def regenerate(
        self,
        employee_id: UUID,
        retail_point_id: UUID,
    ) -> str:
        logger.info(
            "Regenerating invite code",
            retail_point_id=str(retail_point_id),
        )

        await self._validate_employee(employee_id)
        await self._validate_retail_point(retail_point_id)

        invite_code = await self._uow.invite_codes.get_by_retail_point(retail_point_id)

        if invite_code is None:
            logger.warning(
                "Invite code not found for regeneration",
                retail_point_id=str(retail_point_id),
            )
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

        logger.info(
            "Invite code successfully regenerated",
            retail_point_id=str(retail_point_id),
        )
        invite_code_operations_total.labels(action="regenerate").inc()

        return raw_code

    async def activate(
        self,
        raw_code: str,
        client_id: UUID,
    ) -> ClientInviteCode:
        logger.info(
            "Activating invite code",
            client_id=str(client_id),
        )

        invite_code = await self._uow.invite_codes.get_by_code_hash(
            SecurityUtils.hash_invite_code(raw_code)
        )

        if invite_code is None:
            logger.warning(
                "Invite code not found for activation",
                client_id=str(client_id),
            )
            raise InvalidInviteCodeError("Invite code not found")

        try:
            invite_code.activate(client_id)
        except ValueError:
            logger.warning(
                "Failed to activate invite code: invalid or expired",
                client_id=str(client_id),
                invite_code_id=str(invite_code.id),
                retail_point_id=str(invite_code.retail_point_id),
            )
            raise InvalidInviteCodeError("Invite code is invalid or expired")

        await self._uow.invite_codes.update(invite_code)
        await self._uow.commit()

        logger.info(
            "Invite code successfully activated",
            client_id=str(client_id),
            invite_code_id=str(invite_code.id),
            retail_point_id=str(invite_code.retail_point_id),
        )
        invite_code_operations_total.labels(action="activate").inc()

        return invite_code

    async def deactivate(
        self,
        invite_code_id: UUID,
    ) -> ClientInviteCode:
        logger.info(
            "Deactivating invite code",
            invite_code_id=str(invite_code_id),
        )

        invite_code = await self._uow.invite_codes.get_by_id(invite_code_id)

        if invite_code is None:
            logger.warning(
                "Invite code not found for deactivation",
                invite_code_id=str(invite_code_id),
            )
            raise InvalidInviteCodeError("Invite code not found")

        invite_code.deactivate()

        await self._uow.invite_codes.update(invite_code)
        await self._uow.commit()

        logger.info(
            "Invite code successfully deactivated",
            invite_code_id=str(invite_code_id),
            retail_point_id=str(invite_code.retail_point_id),
        )
        invite_code_operations_total.labels(action="deactivate").inc()

        return invite_code

    async def get(
        self,
        invite_code_id: UUID,
    ) -> ClientInviteCode:
        invite_code = await self._uow.invite_codes.get_by_id(invite_code_id)

        if invite_code is None:
            logger.warning(
                "Invite code not found",
                invite_code_id=str(invite_code_id),
            )
            raise InvalidInviteCodeError("Invite code not found")

        return invite_code

    async def get_by_retail_point(
        self,
        retail_point_id: UUID,
    ) -> ClientInviteCode:
        invite_code = await self._uow.invite_codes.get_by_retail_point(retail_point_id)

        if invite_code is None:
            logger.warning(
                "Invite code not found for retail point",
                retail_point_id=str(retail_point_id),
            )
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

    async def create_many(
        self,
        employee_id: UUID,
        retail_point_ids: list[UUID],
    ) -> None:
        logger.info(
            "Creating multiple invite codes",
            count=len(retail_point_ids),
        )

        invite_codes: list[ClientInviteCode] = []

        for point_id in retail_point_ids:
            _, encrypted_code, code_hash = SecurityUtils.generate_invite_code()

            invite_code = ClientInviteCode.create(
                retail_point_id=point_id,
                created_by_employee_id=employee_id,
                encrypted_code=encrypted_code,
                code_hash=code_hash,
            )

            invite_codes.append(invite_code)

        await self._uow.invite_codes.add_many(invite_codes)

        logger.info(
            "Multiple invite codes created successfully",
            created_count=len(invite_codes),
        )
        invite_code_operations_total.labels(action="create_many").inc(len(invite_codes))