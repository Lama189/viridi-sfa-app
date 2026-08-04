from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.visit_debts import VisitDebtService
from app.core.exceptions import VisitDebtNotFoundError


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.visit_debts = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return VisitDebtService(mock_uow)


# --- add ---

@pytest.mark.asyncio
async def test_add_success(service, mock_uow):
    visit_id = uuid4()
    mock_uow.visit_debts.add.return_value = None

    result = await service.add(visit_id, Decimal("50000.00"), "Test debt")

    assert result.visit_id == visit_id
    assert result.amount == Decimal("50000.00")
    assert result.comment == "Test debt"
    mock_uow.visit_debts.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_without_comment(service, mock_uow):
    visit_id = uuid4()
    mock_uow.visit_debts.add.return_value = None

    result = await service.add(visit_id, Decimal("10000.00"))

    assert result.visit_id == visit_id
    assert result.amount == Decimal("10000.00")
    assert result.comment is None


# --- update ---

@pytest.mark.asyncio
async def test_update_success(service, mock_uow):
    from app.domain.entities.visit_debts import VisitDebt

    debt_id = uuid4()
    debt = VisitDebt(
        visit_id=uuid4(),
        amount=Decimal("50000.00"),
        comment="Old comment",
        id=debt_id,
    )
    mock_uow.visit_debts.get_by_id.return_value = debt
    mock_uow.visit_debts.update.return_value = None

    result = await service.update(debt_id, Decimal("75000.00"), "Updated")

    assert result.amount == Decimal("75000.00")
    assert result.comment == "Updated"
    mock_uow.visit_debts.update.assert_awaited_once_with(debt)


@pytest.mark.asyncio
async def test_update_not_found(service, mock_uow):
    mock_uow.visit_debts.get_by_id.return_value = None

    with pytest.raises(VisitDebtNotFoundError):
        await service.update(uuid4(), Decimal("10000.00"), "X")


# --- delete ---

@pytest.mark.asyncio
async def test_delete_success(service, mock_uow):
    from app.domain.entities.visit_debts import VisitDebt

    debt_id = uuid4()
    debt = VisitDebt(
        visit_id=uuid4(),
        amount=Decimal("50000.00"),
        comment="To delete",
        id=debt_id,
    )
    mock_uow.visit_debts.get_by_id.return_value = debt
    mock_uow.visit_debts.delete.return_value = None

    await service.delete(debt_id)

    mock_uow.visit_debts.delete.assert_awaited_once_with(debt)


@pytest.mark.asyncio
async def test_delete_not_found(service, mock_uow):
    mock_uow.visit_debts.get_by_id.return_value = None

    with pytest.raises(VisitDebtNotFoundError):
        await service.delete(uuid4())

    mock_uow.visit_debts.delete.assert_not_awaited()


# --- list_by_visit ---

@pytest.mark.asyncio
async def test_list_by_visit(service, mock_uow):
    visit_id = uuid4()
    mock_uow.visit_debts.list_by_visit.return_value = []

    result = await service.list_by_visit(visit_id)

    assert result == []
    mock_uow.visit_debts.list_by_visit.assert_awaited_once_with(visit_id)


# --- get_by_id ---

@pytest.mark.asyncio
async def test_get_by_id_found(service, mock_uow):
    from app.domain.entities.visit_debts import VisitDebt

    debt_id = uuid4()
    debt = VisitDebt(
        visit_id=uuid4(),
        amount=Decimal("50000.00"),
        comment="Found",
        id=debt_id,
    )
    mock_uow.visit_debts.get_by_id.return_value = debt

    result = await service.get_by_id(debt_id)

    assert result.id == debt_id


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    mock_uow.visit_debts.get_by_id.return_value = None

    with pytest.raises(VisitDebtNotFoundError):
        await service.get_by_id(uuid4())
