from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.visit_debts import VisitDebt
from app.infrastructure.postgres.repos.visit_debts import PostgresVisitDebtRepository


@pytest.mark.asyncio
async def test_visit_debt_repo_operations(session: AsyncSession):
    repo = PostgresVisitDebtRepository(session)
    visit_id = uuid4()

    debt = VisitDebt(visit_id=visit_id, amount=Decimal("1500.00"), comment="Unpaid invoice")
    await repo.add(debt)
    await session.commit()

    found = await repo.get_by_id(debt.id)
    assert found is not None
    assert found.visit_id == visit_id
    assert found.amount == Decimal("1500.00")

    list_debts = await repo.list_by_visit(visit_id)
    assert len(list_debts) == 1

    debt.amount = Decimal("2000.00")
    await repo.update(debt)
    await session.commit()

    updated = await repo.get_by_id(debt.id)
    assert updated.amount == Decimal("2000.00")

    await repo.delete(debt)
    await session.commit()

    deleted = await repo.get_by_id(debt.id)
    assert deleted is None
