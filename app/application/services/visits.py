from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.application.interfaces.services.visit_debts import IVisitDebtService
from app.application.interfaces.services.visit_media import IVisitMediaService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import (
    EmployeeHasActiveVisitError,
    MediaNotFoundError,
    RetailPointInactiveError,
    RetailPointNotFoundError,
    VisitNotActiveError,
    VisitNotFoundError,
)
from app.domain.entities.visit_debts import VisitDebt
from app.domain.entities.visit_media import VisitMedia
from app.domain.entities.visits import Visit
from app.domain.enums import VisitStatus


class VisitService:
    def __init__(
        self,
        uow: IUnitOfWork,
        visit_media_service: IVisitMediaService,
        visit_debts_service: IVisitDebtService,
    ) -> None:
        self._uow = uow
        self._visit_media_service = visit_media_service
        self._visit_debts_service = visit_debts_service

    async def _validate_retail_point(
        self,
        retail_point_id: UUID,
    ) -> None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)

        if retail_point is None:
            raise RetailPointNotFoundError()

        if not retail_point.is_active:
            raise RetailPointInactiveError()

    async def _validate_media_object(
        self,
        media_id: UUID,
    ) -> None:
        media_object = await self._uow.media_objects.get_by_id(media_id)
        if media_object is None:
            raise MediaNotFoundError()

    async def start_visit(self, employee_id: UUID, retail_point_id: UUID) -> Visit:
        await self._validate_retail_point(retail_point_id)

        active_visit = await self._uow.visits.list_by_employee(employee_id, True, 1)
        if active_visit:
            raise EmployeeHasActiveVisitError()

        visit = Visit(
            employee_id=employee_id,
            retail_point_id=retail_point_id,
            started_at=datetime.now(UTC),
        )

        await self._uow.visits.add(visit)

        await self._uow.commit()

        return visit

    async def finish_visit(self, visit_id: UUID) -> Visit:
        visit = await self._uow.visits.get_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        visit.finish()
        await self._uow.visits.update(visit)

        await self._uow.commit()

        return visit

    async def cancel_visit(self, visit_id: UUID) -> Visit:
        visit = await self._uow.visits.get_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        visit.cancel()
        await self._uow.visits.update(visit)

        await self._uow.commit()

        return visit

    async def get_visit(self, visit_id: UUID) -> Visit:
        visit = await self._uow.visits.get_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        return visit

    async def get_visit_details(self, visit_id: UUID):
        visit = await self._uow.visits.get_details_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        return visit

    async def list(
        self,
        employee_id: UUID | None = None,
        retail_point_id: UUID | None = None,
        status: VisitStatus | None = None,
    ) -> list[Visit]:
        if retail_point_id:
            await self._validate_retail_point(retail_point_id)

        return await self._uow.visits.list(employee_id, retail_point_id, status)

    async def attach_media(self, visit_id: UUID, media_id: UUID) -> VisitMedia:
        await self._validate_media_object(media_id)

        visit = await self._uow.visits.get_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        if not visit.can_attach_media:
            raise VisitNotActiveError()

        media = await self._visit_media_service.attach(visit_id, media_id)

        await self._uow.commit()

        return media

    async def detach_media(self, visit_id: UUID, media_id: UUID) -> None:
        await self._validate_media_object(media_id)

        visit = await self._uow.visits.get_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        await self._visit_media_service.detach(visit_id, media_id)

        await self._uow.commit()

    async def add_debt(
        self, visit_id: UUID, amount: Decimal, comment: str | None
    ) -> VisitDebt:
        visit = await self._uow.visits.get_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        if not visit.can_add_debt():
            raise VisitNotActiveError()

        debt = await self._visit_debts_service.add(visit_id, amount, comment)

        await self._uow.commit()

        return debt

    async def update_debt(
        self, visit_debt_id: UUID, amount: Decimal, comment: str | None
    ) -> VisitDebt:
        debt = await self._visit_debts_service.get_by_id(visit_debt_id)
        await self._visit_debts_service.update(visit_debt_id, amount, comment)

        await self._uow.commit()

        return debt

    async def delete_debt(self, visit_debt_id: UUID) -> None:
        await self._visit_debts_service.get_by_id(visit_debt_id)
        await self._visit_debts_service.delete(visit_debt_id)

        await self._uow.commit()
