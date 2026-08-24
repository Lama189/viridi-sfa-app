from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.application.dto.orders import OrderShortDTO
from app.application.dto.retail_points import RetailPointShortDTO
from app.application.dto.visits import (
    VisitDebtDTO,
    VisitDetailsDTO,
    VisitMediaDTO,
)
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
from app.domain.enums import OrderStatus, VisitStatus

ACTIVE_ORDER_STATUSES = [
    OrderStatus.PENDING,
    OrderStatus.CONFIRMED,
    OrderStatus.ASSEMBLY_STARTED,
    OrderStatus.ASSEMBLED,
    OrderStatus.LOADED,
    OrderStatus.SHIPPED,
]


def _order_to_short_dto(order) -> OrderShortDTO:
    return OrderShortDTO(
        id=order.id,
        status=order.status,
        total_amount=order.total_amount,
        total_volume=order.total_volume,
        created_at=getattr(order, "created_at", None),
    )


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

    async def get_visit_details(self, visit_id: UUID) -> VisitDetailsDTO:
        visit = await self._uow.visits.get_details_by_id(visit_id)
        if not visit:
            raise VisitNotFoundError()

        # 1. Created orders in this visit
        created_orders = await self._uow.orders.list_by_source_visit(visit_id)

        # 2. Delivery orders for this visit (planned for this employee & date for this point + delivered in this visit)
        delivery_orders = []
        if visit.started_at:
            plan = await self._uow.visit_plans.get_by_employee_and_date(
                visit.employee_id, visit.started_at.date()
            )
            if plan:
                planned = await self._uow.orders.list_by_planned_visit(plan.id)
                delivery_orders = [
                    o
                    for o in planned
                    if o.retail_point_id == visit.retail_point_id
                    and (
                        o.status != OrderStatus.DELIVERED
                        or o.actual_visit_id == visit_id
                    )
                ]

        delivered_in_visit = await self._uow.orders.list_by_actual_visit(visit_id)
        delivery_map = {o.id: o for o in delivery_orders}
        for o in delivered_in_visit:
            delivery_map[o.id] = o
        delivery_orders = list(delivery_map.values())

        # 3. Active orders of this retail point (excluding delivery and created orders)
        all_active = await self._uow.orders.list_by_retail_point(
            visit.retail_point_id, statuses=ACTIVE_ORDER_STATUSES
        )
        excluded_ids = {o.id for o in created_orders} | {o.id for o in delivery_orders}
        active_point_orders = [o for o in all_active if o.id not in excluded_ids]

        rp = visit.retail_point
        retail_point_dto = RetailPointShortDTO(
            id=rp.id,
            name=rp.name,
            address=rp.address,
            latitude=rp.latitude,
            longitude=rp.longitude,
        )

        created_dtos = [_order_to_short_dto(o) for o in created_orders]
        delivery_dtos = [_order_to_short_dto(o) for o in delivery_orders]
        active_dtos = [_order_to_short_dto(o) for o in active_point_orders]

        debt_dtos = [
            VisitDebtDTO(
                id=d.id,
                visit_id=d.visit_id,
                amount=d.amount,
                comment=d.comment,
                created_at=getattr(d, "created_at", None),
            )
            for d in (getattr(visit, "debts", None) or [])
        ]
        media_dtos = [
            VisitMediaDTO(
                id=m.id,
                visit_id=m.visit_id,
                media_id=m.media_id,
                created_at=getattr(m, "created_at", None),
            )
            for m in (getattr(visit, "media", None) or [])
        ]

        return VisitDetailsDTO(
            id=visit.id,
            status=visit.status,
            retail_point=retail_point_dto,
            started_at=visit.started_at,
            finished_at=visit.finished_at,
            created_orders=created_dtos,
            delivery_orders=delivery_dtos,
            active_point_orders=active_dtos,
            debts=debt_dtos,
            media=media_dtos,
            orders=created_dtos,
        )

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
