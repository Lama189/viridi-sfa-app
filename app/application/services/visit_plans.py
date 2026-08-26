from datetime import date
from uuid import UUID

from app.application.dto.retail_points import RetailPointShortDTO
from app.application.dto.visit_plans import VisitPlanDTO, VisitPlanItemDTO
from app.application.interfaces.services.visit_plans import IVisitPlanService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import (
    VisitPlanAlreadyExistsError,
    VisitPlanNotFoundError,
)
from app.domain.entities.visit_plan_items import VisitPlanItem
from app.domain.entities.visit_plans import VisitPlan
from app.domain.enums import Weekday


class VisitPlanService(IVisitPlanService):
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_plan(
        self,
        plan: VisitPlan,
    ) -> VisitPlan:
        await self._uow.visit_plans.add(plan)
        if plan.items:
            await self._uow.visit_plan_items.add_many(plan.items)

        await self._uow.commit()

        return plan

    async def generate_for_employee(
        self,
        employee_id: UUID,
        plan_date: date,
        overwrite: bool = True,
    ) -> VisitPlan:
        existing = await self._uow.visit_plans.get_by_employee_and_date(
            employee_id, plan_date
        )
        if existing:
            if not overwrite:
                raise VisitPlanAlreadyExistsError()
            await self._uow.visit_plan_items.delete_by_plan(existing.id)
            plan = existing
            plan.items = []
        else:
            plan = VisitPlan(
                employee_id=employee_id,
                plan_date=plan_date,
            )

        weekday = Weekday(plan_date.weekday())

        retail_points = await self._uow.retail_points.list_by_employee_and_weekday(
            employee_id, weekday
        )

        for position, retail_point in enumerate(
            sorted(retail_points, key=lambda rp: rp.address),
            start=1,
        ):
            plan.add_item(
                VisitPlanItem(
                    visit_plan_id=plan.id,
                    retail_point_id=retail_point.id,
                    order=position,
                )
            )

        if not existing:
            return await self.create_plan(plan)

        if plan.items:
            await self._uow.visit_plan_items.add_many(plan.items)

        await self._uow.commit()

        return plan

    async def get_by_employee_and_date(
        self,
        employee_id: UUID,
        plan_date: date,
    ) -> VisitPlan:
        plan = await self._uow.visit_plans.get_by_employee_and_date(
            employee_id, plan_date
        )
        if plan is None:
            raise VisitPlanNotFoundError()

        plan.items = await self._uow.visit_plan_items.list_by_plan(
            plan.id,
        )

        return plan

    async def get_today_plan(
        self,
        employee_id: UUID,
    ) -> VisitPlan:
        return await self.get_by_employee_and_date(
            employee_id,
            date.today(),
        )

    async def enrich_plan(self, plan: VisitPlan) -> VisitPlanDTO:
        rp_ids = [item.retail_point_id for item in plan.items]
        retail_points = await self._uow.retail_points.list_by_ids(rp_ids)
        rp_map = {rp.id: rp for rp in retail_points}

        items_dto: list[VisitPlanItemDTO] = []
        for item in plan.items:
            rp = rp_map.get(item.retail_point_id)
            rp_dto = (
                RetailPointShortDTO(
                    id=rp.id,
                    name=rp.name,
                    address=rp.address,
                    contact_person=rp.contact_person,
                    phone_number=rp.phone_number,
                    latitude=rp.latitude,
                    longitude=rp.longitude,
                )
                if rp
                else None
            )
            items_dto.append(
                VisitPlanItemDTO(
                    order=item.order,
                    status=item.status,
                    retail_point_id=item.retail_point_id,
                    retail_point=rp_dto,
                )
            )

        return VisitPlanDTO(
            id=plan.id,
            employee_id=plan.employee_id,
            date=plan.plan_date,
            weekday=plan.weekday,
            status=plan.status,
            items=items_dto,
        )

    async def get_today_plan_dto(self, employee_id: UUID) -> VisitPlanDTO:
        plan = await self.get_today_plan(employee_id)
        return await self.enrich_plan(plan)

    async def get_plan_by_date_dto(
        self, employee_id: UUID, plan_date: date
    ) -> VisitPlanDTO:
        plan = await self.get_by_employee_and_date(employee_id, plan_date)
        return await self.enrich_plan(plan)

    async def generate_for_employee_dto(
        self, employee_id: UUID, plan_date: date, overwrite: bool = True
    ) -> VisitPlanDTO:
        plan = await self.generate_for_employee(
            employee_id, plan_date, overwrite=overwrite
        )
        return await self.enrich_plan(plan)
