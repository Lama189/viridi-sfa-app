from abc import ABC, abstractmethod
from uuid import UUID

from app.api.v1.schemas.retail_points import VisitsDatesDTO
from app.domain.entities.visit_schedule_rules import VisitScheduleRule
from app.domain.enums import Weekday


class IVisitScheduleService(ABC):
    @abstractmethod
    async def replace_schedule(
        self,
        retail_point_id: UUID,
        dto: VisitsDatesDTO,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def add_weekday(
        self,
        retail_point_id: UUID,
        weekday: Weekday,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def remove_weekday(
        self,
        retail_point_id: UUID,
        weekday: Weekday,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def activate_rule(
        self,
        rule_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def deactivate_rule(
        self,
        rule_id: UUID,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_schedule(
        self,
        retail_point_id: UUID,
    ) -> list[VisitScheduleRule]:
        raise NotImplementedError

    @abstractmethod
    async def get_active_rules_by_weekday(
        self,
        weekday: Weekday,
    ) -> list[VisitScheduleRule]:
        raise NotImplementedError
