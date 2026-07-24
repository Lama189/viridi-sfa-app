from decimal import Decimal
from uuid import uuid4

import pytest

from app.domain.entities.visit_debts import VisitDebt


def test_visit_debt_default_values():
    visit_id = uuid4()
    debt = VisitDebt(visit_id=visit_id, amount=Decimal("100.00"), comment="Test")
    assert debt.visit_id == visit_id
    assert debt.amount == Decimal("100.00")
    assert debt.comment == "Test"
    assert isinstance(debt.id, type(uuid4()))
    assert debt.created_at is not None


def test_visit_debt_zero_amount():
    debt = VisitDebt(visit_id=uuid4(), amount=Decimal("0"), comment=None)
    assert debt.amount == Decimal("0")


def test_visit_debt_negative_amount_raises():
    with pytest.raises(ValueError, match="negative"):
        VisitDebt(visit_id=uuid4(), amount=Decimal("-10"), comment=None)


def test_visit_debt_change_amount():
    debt = VisitDebt(visit_id=uuid4(), amount=Decimal("100"), comment=None)
    debt.change_amount(Decimal("250.50"))
    assert debt.amount == Decimal("250.50")


def test_visit_debt_change_amount_zero_raises():
    debt = VisitDebt(visit_id=uuid4(), amount=Decimal("100"), comment=None)
    with pytest.raises(ValueError, match="greater than zero"):
        debt.change_amount(Decimal("0"))


def test_visit_debt_change_amount_negative_raises():
    debt = VisitDebt(visit_id=uuid4(), amount=Decimal("100"), comment=None)
    with pytest.raises(ValueError, match="greater than zero"):
        debt.change_amount(Decimal("-50"))


def test_visit_debt_change_comment():
    debt = VisitDebt(visit_id=uuid4(), amount=Decimal("100"), comment="Old")
    debt.change_comment("New comment")
    assert debt.comment == "New comment"


def test_visit_debt_change_comment_to_none():
    debt = VisitDebt(visit_id=uuid4(), amount=Decimal("100"), comment="Old")
    debt.change_comment(None)
    assert debt.comment is None
