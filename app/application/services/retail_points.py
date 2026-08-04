from uuid import UUID

from app.core.observability.logging import logger
from app.core.observability.metrics import (
    retail_point_operations_total,
    media_operations_total,
)

from app.domain.entities.retail_points import (
    RetailPoint, 
    RetailPointIdentity, 
    BulkCreateRetailPointsResult
)

from app.application.interfaces.uow import IUnitOfWork
from app.application.interfaces.services.invite_codes import IClientInviteCodesService
from app.application.interfaces.services.retail_point_assignments import IRetailPointAssignmentService
from app.application.interfaces.services.visit_schedule_rules import IVisitScheduleService

from app.api.v1.schemas.retail_points import CreateRetailPointRequest, UpdateRetailPointRequest
from app.domain.enums import Weekday
from app.core.exceptions import (
    RetailPointNotFoundError, 
    RetailPointAlreadyExistsError,
    RetailPointImageNotFoundError, 
    RetailPointImageAlreadyExistsError,
    DuplicateRetailPointError,
    BulkCreateRetailPointsRequestIsEmptyError
)


class RetailPointsService:

    def __init__(
        self, 
        uow: IUnitOfWork, 
        invite_codes_service: IClientInviteCodesService,
        assignments_service: IRetailPointAssignmentService,
        visits_rules_service: IVisitScheduleService,
    ) -> None:
        self._uow = uow
        self._invite_codes_service = invite_codes_service
        self._assignments_service = assignments_service
        self._visits_rules_service = visits_rules_service

    async def create_retail_point(
        self,
        dto: CreateRetailPointRequest,
        employee_id: UUID,
    ) -> tuple[RetailPoint, str]:
        point = RetailPoint(
            name=dto.name,
            address=dto.address,
            legal_name=dto.legal_name,
            client_type=dto.client_type,
            landmark=dto.landmark,
            contact_person=dto.contact_person,
            phone_number=dto.phone_number,
            inn=dto.inn,
            checking_account=dto.checking_account,
            bank_name=dto.bank_name,
            mfo=dto.mfo,
            oked=dto.oked,
            latitude=dto.latitude,
            longitude=dto.longitude,
            photo_id=dto.photo_id,
            created_by_employee_id=employee_id,
            is_active=True,
        )

        await self._uow.retail_points.add(point)

        await self._visits_rules_service.replace_schedule(point.id, dto.visits)
        code = await self._invite_codes_service.create(employee_id, point.id)
        await self._assignments_service.create(point.id)

        await self._uow.commit()

        logger.info("Retail point succesfully created", retail_point_id=str(point.id))
        retail_point_operations_total.labels(action="create").inc()

        return point, code
    
    async def update_retail_point(
        self,
        retail_point_id: UUID,
        dto: UpdateRetailPointRequest,
    ) -> RetailPoint:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if not retail_point:
            logger.warning(
                "Retail point not found for update",
                retail_point_id=str(retail_point_id)
            )
            raise ValueError(f"Retail point {retail_point_id} not found")

        if dto.name is not None:
            retail_point.name = dto.name
        if dto.legal_name is not None:
            retail_point.legal_name = dto.legal_name
        if dto.client_type is not None:
            retail_point.client_type = dto.client_type
        if dto.address is not None:
            retail_point.address = dto.address
        if dto.landmark is not None:
            retail_point.landmark = dto.landmark
        if dto.contact_person is not None:
            retail_point.contact_person = dto.contact_person
        if dto.phone_number is not None:
            retail_point.phone_number = dto.phone_number
        if dto.inn is not None:
            retail_point.inn = dto.inn
        if dto.checking_account is not None:
            retail_point.checking_account = dto.checking_account
        if dto.bank_name is not None:
            retail_point.bank_name = dto.bank_name
        if dto.mfo is not None:
            retail_point.mfo = dto.mfo
        if dto.oked is not None:
            retail_point.oked = dto.oked
        if dto.latitude is not None:
            retail_point.latitude = dto.latitude
        if dto.longitude is not None:
            retail_point.longitude = dto.longitude
        if dto.photo_id is not None:
            retail_point.photo_id = dto.photo_id
        if dto.is_active is not None:
            retail_point.is_active = bool(dto.is_active)

        await self._uow.retail_points.update(retail_point)

        if dto.visits is not None:
            await self._visits_rules_service.replace_schedule(retail_point.id, dto.visits)

        await self._uow.commit()

        logger.info("Retail point succesfully updated", retail_point_id=str(retail_point.id))
        retail_point_operations_total.labels(action="update").inc()

        return retail_point

    async def delete_retail_point(self, retail_point_id: UUID) -> None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if not retail_point:
            logger.warning(
                "Retail point not found for deletion",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointNotFoundError()

        await self._uow.retail_points.delete(retail_point)
        await self._assignments_service.delete(retail_point_id)
        
        await self._uow.commit()

        logger.info("Retail point deleted", retail_point_id=str(retail_point_id))
        retail_point_operations_total.labels(action="delete").inc()

    async def get_by_id(self, retail_point_id: UUID) -> RetailPoint:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if not retail_point:
            logger.warning(
                "Retail point not found",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointNotFoundError()
        
        return retail_point

    async def get_retail_point_invite_code(self, retail_point_id: UUID) -> str | None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if retail_point is None:
            logger.warning(
                "Retail point not found when getting invite code",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointNotFoundError()

        return await self._invite_codes_service.get_raw_code(retail_point_id)

    async def detach_media(self, retail_point_id: UUID) -> UUID:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if retail_point is None:
            logger.warning("Retail point not found", retail_point_id=str(retail_point_id))
            raise RetailPointNotFoundError()

        if retail_point.photo_id is None:
            logger.warning("Retail point image not found to detach", retail_point_id=str(retail_point_id))
            raise RetailPointImageNotFoundError()

        media_id, retail_point.photo_id = retail_point.photo_id, None

        await self._uow.retail_points.update(retail_point)
        await self._uow.commit()

        logger.info(
            "Media successfully detached",
            retail_point_id=str(retail_point_id),
            detached_media_id=str(media_id),
        )
        media_operations_total.labels(action="detach").inc()

        return media_id

    async def change_media(self, retail_point_id: UUID, new_media_id: UUID) -> UUID:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        exists = await self._uow.media_objects.exists_by(id=new_media_id)

        if retail_point is None:
            logger.warning("Retail point not found", retail_point_id=str(retail_point_id))
            raise RetailPointNotFoundError()

        if retail_point.photo_id is None or not exists:
            logger.warning(
                "Cannot change media: current photo is missing or new media object does not exist",
                retail_point_id=str(retail_point_id),
                new_media_id=str(new_media_id),
                has_current_photo=bool(retail_point.photo_id),
                new_media_exists=exists,
            )
            raise RetailPointImageNotFoundError()


        old_media_id, retail_point.photo_id = retail_point.photo_id, new_media_id

        await self._uow.retail_points.update(retail_point)
        await self._uow.commit()

        logger.info(
            "Media successfully changed",
            retail_point_id=str(retail_point_id),
            old_media_id=str(old_media_id),
            new_media_id=str(new_media_id),
        )
        media_operations_total.labels(action="change").inc()

        return old_media_id

    async def setup_media(self, retail_point_id: UUID, media_id: UUID) -> UUID:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if retail_point is None:
            logger.warning("Retail point not found", retail_point_id=str(retail_point_id))
            raise RetailPointNotFoundError()

        if retail_point.photo_id is not None:
            logger.warning(
                "Retail point already has a photo",
                retail_point_id=str(retail_point_id),
                existing_photo_id=str(retail_point.photo_id),
            )
            raise RetailPointImageAlreadyExistsError()
        
        exists = await self._uow.media_objects.exists_by(id=media_id)
        if not exists:
            logger.warning(
                "Media object does not exist",
                media_id=str(media_id),
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointImageNotFoundError()

        retail_point.photo_id = media_id

        await self._uow.retail_points.update(retail_point)
        await self._uow.commit()

        logger.info(
            "Media successfully set up",
            retail_point_id=str(retail_point_id),
            media_id=str(media_id),
        )
        media_operations_total.labels(action="attach").inc()
        
        return media_id

    async def list_by_employee(self, employee_id: UUID) -> list[RetailPoint]:
        return await self._uow.retail_points.list_by_employee(employee_id, True)

    async def list_by_employee_and_weekday(
        self,
        employee_id: UUID,
        weekday: Weekday,
    ) -> list[RetailPoint]:
        return await self._uow.retail_points.list_by_employee_and_weekday(
            employee_id=employee_id,
            weekday=weekday,
            only_active=True,
        )

    async def bulk_create(
        self,
        employee_id: UUID,
        dto: list[CreateRetailPointRequest],
    ) -> BulkCreateRetailPointsResult:
        if not dto:
            logger.warning("Bulk create request is empty", employee_id=str(employee_id))
            raise BulkCreateRetailPointsRequestIsEmptyError()

        retail_points = await self._prepare_bulk_create(employee_id, dto)
        retail_point_ids = [retail_point.id for retail_point in retail_points]

        await self._uow.retail_points.add_many(retail_points)

        for retail_point, point_dto in zip(retail_points, dto):
            await self._visits_rules_service.replace_schedule(
                retail_point.id,
                point_dto.visits,
            )

        await self._invite_codes_service.create_many(employee_id, retail_point_ids)
        await self._assignments_service.create_many(retail_point_ids)

        await self._uow.commit()

        logger.info(
            "Bulk creation completed successfully",
            employee_id=str(employee_id),
            created_count=len(retail_points),
        )
        retail_point_operations_total.labels(action="bulk_create").inc(len(retail_points))

        return BulkCreateRetailPointsResult(created=retail_points)

    async def list_retail_points(
        self,
        employee_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RetailPoint]:
        return await self._uow.retail_points.list_paginated(
            employee_id=employee_id,
            limit=limit,
            offset=offset,
        )

    async def _prepare_bulk_create(
        self,
        employee_id: UUID,
        dto: list[CreateRetailPointRequest],
    ) -> list[RetailPoint]:
        identities: set[RetailPointIdentity] = set()

        for point in dto:
            identity = RetailPointIdentity(
                name=point.name,
                address=point.address,
            )

            if identity in identities:
                logger.warning(
                    "Duplicate retail point in bulk payload",
                    employee_id=str(employee_id),
                    duplicate_name=point.name,
                    duplicate_address=point.address,
                )
                raise DuplicateRetailPointError()

            identities.add(identity)

        existing = await self._uow.retail_points.find_existing_by_identity(list(identities))
        if existing:
            logger.warning(
                "Retail point already exists in DB during bulk create",
                employee_id=str(employee_id),
                existing_count=len(existing),
            )
            raise RetailPointAlreadyExistsError(existing)

        return [
            RetailPoint(
                name=point.name,
                address=point.address,
                legal_name=point.legal_name,
                client_type=point.client_type,
                landmark=point.landmark,
                contact_person=point.contact_person,
                phone_number=point.phone_number,
                inn=point.inn,
                checking_account=point.checking_account,
                bank_name=point.bank_name,
                mfo=point.mfo,
                oked=point.oked,
                latitude=point.latitude,
                longitude=point.longitude,
                photo_id=point.photo_id,
                created_by_employee_id=employee_id,
            )
            for point in dto
        ]