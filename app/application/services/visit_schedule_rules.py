from uuid import UUID

from app.api.v1.schemas.retail_points import VisitsDatesDTO
from app.application.interfaces.services.visit_schedule_rules import IVisitScheduleService
from app.application.interfaces.uow import IUnitOfWork
from app.domain.entities.visit_schedule_rules import VisitScheduleRule
from app.domain.enums import Weekday


class VisitScheduleService(IVisitScheduleService):

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def replace_schedule(
        self,
        retail_point_id: UUID,
        dto: VisitsDatesDTO,
    ) -> None:
        rules = [
            VisitScheduleRule(
                retail_point_id=retail_point_id,
                weekday=weekday,
            )
            for weekday, enabled in self._mapping(dto).items()
            if enabled
        ]

        await self._uow.visit_schedule_rules.replace_for_retail_point(
            retail_point_id,
            rules,
        )
        await self._uow.commit()

    async def add_weekday(
        self,
        retail_point_id: UUID,
        weekday: Weekday,
    ) -> None:
        rules = await self._uow.visit_schedule_rules.list_by_retail_point(
            retail_point_id,
        )

        existing = self._find_rule_by_weekday(rules, weekday)

        if existing:
            if not existing.is_active:
                existing.activate()
                await self._uow.visit_schedule_rules.replace_for_retail_point(
                    retail_point_id,
                    rules,
                )
                await self._uow.commit()

            return

        await self._uow.visit_schedule_rules.add(
            VisitScheduleRule(
                retail_point_id=retail_point_id,
                weekday=weekday,
            )
        )

        await self._uow.commit()

    async def remove_weekday(
        self,
        retail_point_id: UUID,
        weekday: Weekday,
    ) -> None:
        rules = await self._uow.visit_schedule_rules.list_by_retail_point(
            retail_point_id,
        )

        rule = self._find_rule_by_weekday(rules, weekday)

        if rule is None:
            return

        await self._uow.visit_schedule_rules.delete(rule)
        await self._uow.commit()

    async def activate_rule(
        self,
        rule_id: UUID,
    ) -> None:
        await self._change_activity(rule_id, True)

    async def deactivate_rule(
        self,
        rule_id: UUID,
    ) -> None:
        await self._change_activity(rule_id, False)

    async def get_schedule(
        self,
        retail_point_id: UUID,
    ) -> list[VisitScheduleRule]:
        return await self._uow.visit_schedule_rules.list_by_retail_point(
            retail_point_id,
        )

    async def get_active_rules_by_weekday(
        self,
        weekday: Weekday,
    ) -> list[VisitScheduleRule]:
        return await self._uow.visit_schedule_rules.get_active_rules_by_weekday(
            weekday
        )

    async def _change_activity(
        self,
        rule_id: UUID,
        is_active: bool,
    ) -> None:
        rule = await self._uow.visit_schedule_rules.get_by_id(rule_id)

        if rule is None:
            raise ValueError(f"Visit schedule rule {rule_id} not found")

        if rule.is_active == is_active:
            return

        if is_active:
            rule.activate()
        else:
            rule.deactivate()

        await self._uow.visit_schedule_rules.update(rule)
        await self._uow.commit()

    def _find_rule_by_weekday(
        self,
        rules: list[VisitScheduleRule],
        weekday: Weekday,
    ) -> VisitScheduleRule | None:
        return next(
            (rule for rule in rules if rule.weekday == weekday),
            None,
        )

    def _mapping(
        self,
        dto: VisitsDatesDTO,
    ) -> dict[Weekday, bool]:
        return {
            Weekday.MONDAY: dto.mon,
            Weekday.TUESDAY: dto.tue,
            Weekday.WEDNESDAY: dto.wed,
            Weekday.THURSDAY: dto.thu,
            Weekday.FRIDAY: dto.fri,
            Weekday.SATURDAY: dto.sat,
            Weekday.SUNDAY: dto.sun,
        }