from uuid import uuid4

from app.domain.entities.visit_schedule_rules import VisitScheduleRule
from app.domain.enums import Weekday


def test_visit_schedule_rule_defaults_and_activation():
    point_id = uuid4()
    rule = VisitScheduleRule(retail_point_id=point_id, weekday=Weekday.MONDAY)

    assert rule.retail_point_id == point_id
    assert rule.weekday == Weekday.MONDAY
    assert rule.is_active is True
    assert isinstance(rule.id, type(uuid4()))

    rule.deactivate()
    assert rule.is_active is False

    rule.activate()
    assert rule.is_active is True
