from uuid import uuid4

import pytest

from app.domain.entities.visits import Visit
from app.domain.enums import VisitStatus


def test_visit_default_values():
    employee_id = uuid4()
    retail_point_id = uuid4()
    v = Visit(employee_id=employee_id, retail_point_id=retail_point_id)
    assert v.employee_id == employee_id
    assert v.retail_point_id == retail_point_id
    assert isinstance(v.id, type(uuid4()))
    assert v.status == VisitStatus.IN_PROGRESS
    assert v.started_at is None
    assert v.finished_at is None


def test_visit_start():
    v = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    v.start()
    assert v.started_at is not None
    assert v.status == VisitStatus.IN_PROGRESS


def test_visit_finish():
    v = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    v.start()
    v.finish()
    assert v.finished_at is not None
    assert v.status == VisitStatus.COMPLETED


def test_visit_cancel():
    v = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    v.start()
    v.cancel()
    assert v.finished_at is not None
    assert v.status == VisitStatus.CANCELLED


def test_visit_is_active():
    v = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    assert v.is_active is False
    assert v.can_attach_media() is True
    assert v.can_add_debt() is False

    v.start()
    assert v.is_active is True
    assert v.can_attach_media() is True
    assert v.can_add_debt() is True

    v.finish()
    assert v.is_active is False
    assert v.can_attach_media() is True
    assert v.can_add_debt() is False


def test_visit_finish_without_start_raises():
    v = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    with pytest.raises(ValueError):
        v.finish()


def test_visit_cancel_completed_raises():
    v = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    v.start()
    v.finish()
    with pytest.raises(ValueError):
        v.cancel()


def test_visit_cancel_already_cancelled_raises():
    v = Visit(employee_id=uuid4(), retail_point_id=uuid4())
    v.start()
    v.cancel()
    with pytest.raises(ValueError):
        v.cancel()
