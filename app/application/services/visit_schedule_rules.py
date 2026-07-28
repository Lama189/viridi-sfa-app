from uuid import UUID

from app.api.v1.schemas.retail_points import VisitsDatesDTO
from app.domain.entities.visit_schedule_rules import VisitScheduleRule
from app.domain.enums import Weekday
from app.application.interfaces.uow import IUnitOfWork


class VisitScheduleService:

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def replace_schedule(
        self,
        retail_point_id: UUID,
        dto: VisitsDatesDTO,
    ) -> None:
        rules = []

        mapping = {
            Weekday.MONDAY: dto.mon,
            Weekday.TUESDAY: dto.tue,
            Weekday.WEDNESDAY: dto.wed,
            Weekday.THURSDAY: dto.thu,
            Weekday.FRIDAY: dto.fri,
            Weekday.SATURDAY: dto.sat,
            Weekday.SUNDAY: dto.sun,
        }

        for weekday, is_active in mapping.items():
            if is_active:
                rules.append(
                    VisitScheduleRule(
                        retail_point_id=retail_point_id,
                        weekday=weekday,
                    )
                )

        await self._uow.visit_schedule_rules.replace_for_retail_point(retail_point_id, rules)