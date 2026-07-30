from uuid import UUID
from datetime import date

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.visit_schedule_rules import IVisitScheduleRuleRepository
from app.domain.entities.visit_schedule_rules import VisitScheduleRule
from app.domain.enums import Weekday
from app.infrastructure.postgres.models.visit_schedule_rules import VisitScheduleRule as VisitScheduleRuleModel


class PostgresVisitScheduleRuleRepository(IVisitScheduleRuleRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, rule: VisitScheduleRule) -> None:
        model = self._to_model(rule)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, rule_id: UUID) -> VisitScheduleRule | None:
        result = await self._session.execute(
            select(VisitScheduleRuleModel).where(VisitScheduleRuleModel.id == rule_id)
        )
        
        model = result.scalar_one_or_none()
        if model is None:
            return None
        
        return self._to_domain(model)

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(VisitScheduleRuleModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def update(self, rule: VisitScheduleRule) -> None:
        await self._session.execute(
            update(VisitScheduleRuleModel)
            .where(VisitScheduleRuleModel.id == rule.id)
            .values(
                retail_point_id=rule.retail_point_id,
                weekday=rule.weekday.value,
                is_active=rule.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, rule: VisitScheduleRule) -> None:
        await self._session.execute(
            sa_delete(VisitScheduleRuleModel).where(VisitScheduleRuleModel.id == rule.id)
        )
        await self._session.flush()

    async def list_by_retail_point(
        self,
        retail_point_id: UUID,
    ) -> list[VisitScheduleRule]:
        result = await self._session.execute(
            select(VisitScheduleRuleModel)
            .where(VisitScheduleRuleModel.retail_point_id == retail_point_id)
            .order_by(VisitScheduleRuleModel.weekday)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_active_rules_by_weekday(
        self,
        weekday: Weekday,
    ) -> list[VisitScheduleRule]:
        result = await self._session.execute(
            select(VisitScheduleRuleModel)
            .where(
                VisitScheduleRuleModel.is_active.is_(True),
                VisitScheduleRuleModel.weekday == weekday.value,
            )
            .order_by(VisitScheduleRuleModel.retail_point_id)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def replace_for_retail_point(
        self,
        retail_point_id: UUID,
        rules: list[VisitScheduleRule],
    ) -> None:
        await self._session.execute(
            sa_delete(VisitScheduleRuleModel)
            .where(VisitScheduleRuleModel.retail_point_id == retail_point_id)
        )
        await self._session.flush()

        models = [self._to_model(rule) for rule in rules]
        self._session.add_all(models)
        await self._session.flush()


    async def get_active_rules_for_day(
        self,
        day: date,
    ) -> list[VisitScheduleRule]:
        result = await self._session.execute(
            select(VisitScheduleRuleModel)
            .where(
                VisitScheduleRuleModel.is_active.is_(True),
                VisitScheduleRuleModel.weekday == day.weekday(),
            )
            .order_by(VisitScheduleRuleModel.retail_point_id)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: VisitScheduleRuleModel) -> VisitScheduleRule:
        return VisitScheduleRule(
            id=model.id,
            retail_point_id=model.retail_point_id,
            weekday=Weekday(model.weekday),
            is_active=model.is_active,
        )

    def _to_model(self, rule: VisitScheduleRule) -> VisitScheduleRuleModel:
        return VisitScheduleRuleModel(
            id=rule.id,
            retail_point_id=rule.retail_point_id,
            weekday=rule.weekday.value,
            is_active=rule.is_active,
        )