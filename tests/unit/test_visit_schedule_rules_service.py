from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.retail_points import VisitsDatesDTO
from app.application.services.visit_schedule_rules import VisitScheduleService
from app.domain.entities.visit_schedule_rules import VisitScheduleRule
from app.domain.enums import Weekday


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.visit_schedule_rules = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return VisitScheduleService(uow=mock_uow)


@pytest.mark.asyncio
async def test_replace_schedule(service, mock_uow):
    point_id = uuid4()
    dto = VisitsDatesDTO(mon=True, wed=True)

    await service.replace_schedule(point_id, dto)

    mock_uow.visit_schedule_rules.replace_for_retail_point.assert_awaited_once()
    args = mock_uow.visit_schedule_rules.replace_for_retail_point.call_args[0]
    assert args[0] == point_id
    assert len(args[1]) == 2
    assert {r.weekday for r in args[1]} == {Weekday.MONDAY, Weekday.WEDNESDAY}
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_weekday_new(service, mock_uow):
    point_id = uuid4()
    mock_uow.visit_schedule_rules.list_by_retail_point.return_value = []

    await service.add_weekday(point_id, Weekday.TUESDAY)

    mock_uow.visit_schedule_rules.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_weekday_existing_inactive(service, mock_uow):
    point_id = uuid4()
    inactive_rule = VisitScheduleRule(
        retail_point_id=point_id, weekday=Weekday.TUESDAY, is_active=False
    )
    mock_uow.visit_schedule_rules.list_by_retail_point.return_value = [inactive_rule]

    await service.add_weekday(point_id, Weekday.TUESDAY)

    assert inactive_rule.is_active is True
    mock_uow.visit_schedule_rules.replace_for_retail_point.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_weekday_exists(service, mock_uow):
    point_id = uuid4()
    rule = VisitScheduleRule(retail_point_id=point_id, weekday=Weekday.FRIDAY)
    mock_uow.visit_schedule_rules.list_by_retail_point.return_value = [rule]

    await service.remove_weekday(point_id, Weekday.FRIDAY)

    mock_uow.visit_schedule_rules.delete.assert_awaited_once_with(rule)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_weekday_not_found(service, mock_uow):
    point_id = uuid4()
    mock_uow.visit_schedule_rules.list_by_retail_point.return_value = []

    await service.remove_weekday(point_id, Weekday.FRIDAY)

    mock_uow.visit_schedule_rules.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_activate_and_deactivate_rule(service, mock_uow):
    rule_id = uuid4()
    rule = VisitScheduleRule(
        retail_point_id=uuid4(), weekday=Weekday.MONDAY, is_active=False, id=rule_id
    )
    mock_uow.visit_schedule_rules.get_by_id.return_value = rule

    await service.activate_rule(rule_id)
    assert rule.is_active is True
    mock_uow.visit_schedule_rules.update.assert_awaited_once_with(rule)

    await service.deactivate_rule(rule_id)
    assert rule.is_active is False
