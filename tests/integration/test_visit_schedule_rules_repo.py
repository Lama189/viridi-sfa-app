from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.visit_schedule_rules import VisitScheduleRule
from app.domain.enums import Weekday
from app.infrastructure.postgres.repos.visits_schedule_rules import (
    PostgresVisitScheduleRuleRepository,
)


@pytest.mark.asyncio
async def test_visit_schedule_rule_repo_operations(session: AsyncSession):
    repo = PostgresVisitScheduleRuleRepository(session)
    point_id = uuid4()

    rule_mon = VisitScheduleRule(retail_point_id=point_id, weekday=Weekday.MONDAY)
    rule_wed = VisitScheduleRule(retail_point_id=point_id, weekday=Weekday.WEDNESDAY)

    await repo.add(rule_mon)
    await repo.add(rule_wed)
    await session.commit()

    rules = await repo.list_by_retail_point(point_id)
    assert len(rules) == 2

    active_mon = await repo.get_active_rules_by_weekday(Weekday.MONDAY)
    assert len(active_mon) >= 1
    assert any(r.retail_point_id == point_id for r in active_mon)

    new_rule_fri = VisitScheduleRule(retail_point_id=point_id, weekday=Weekday.FRIDAY)
    await repo.replace_for_retail_point(point_id, [new_rule_fri])
    await session.commit()

    rules_after_replace = await repo.list_by_retail_point(point_id)
    assert len(rules_after_replace) == 1
    assert rules_after_replace[0].weekday == Weekday.FRIDAY
