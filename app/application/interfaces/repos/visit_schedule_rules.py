from abc import ABC, abstractmethod
from uuid import UUID
from datetime import date

from app.domain.entities.visit_schedule_rules import VisitScheduleRule


class IVisitScheduleRuleRepository(ABC):

    @abstractmethod
    async def add(
        self, 
        rule: VisitScheduleRule
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, rule: VisitScheduleRule) -> None:
        raise NotImplementedError

    @abstractmethod    
    async def list_by_retail_point(
        self,
        retail_point_id: UUID,
    ) -> list[VisitScheduleRule]:
        raise NotImplementedError

    @abstractmethod
    async def get_active_rules_for_day(
        self,
        day: date,
    ) -> list[VisitScheduleRule]:
        raise NotImplementedError

    @abstractmethod
    async def replace_for_retail_point(
        self,
        retail_point_id: UUID,
        rules: list[VisitScheduleRule],
    ) -> None:
        raise NotImplementedError