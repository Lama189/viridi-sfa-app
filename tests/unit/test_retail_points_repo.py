from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.domain.enums import ClientType, OrderStatus
from app.infrastructure.postgres.repos.retail_points import (
    PostgresRetailPointRepository,
)


@pytest.mark.asyncio
async def test_get_details_by_id_returns_retail_point_orders_and_debts():
    retail_point_id = uuid4()
    now = datetime.now(UTC)
    order = SimpleNamespace(
        id=uuid4(),
        warehouse_id=uuid4(),
        created_by_id=uuid4(),
        retail_point_id=retail_point_id,
        visit_id=uuid4(),
        status=OrderStatus.PENDING,
        total_amount=Decimal("250000.00"),
        total_volume=Decimal("2.500"),
        created_at=now,
        updated_at=now,
    )
    debt = SimpleNamespace(
        id=uuid4(),
        visit_id=order.visit_id,
        amount=Decimal("50000.00"),
        comment="Unpaid",
        created_at=now,
    )
    retail_point = SimpleNamespace(
        id=retail_point_id,
        name="Point",
        legal_name=None,
        client_type=ClientType.C,
        address="Address",
        landmark=None,
        contact_person=None,
        phone_number=None,
        inn=None,
        checking_account=None,
        bank_name=None,
        mfo=None,
        oked=None,
        latitude=None,
        longitude=None,
        photo_id=None,
        created_by_employee_id=None,
        is_active=True,
        orders=[order],
        visits=[SimpleNamespace(debts=[debt])],
    )
    result = MagicMock()
    result.unique.return_value.scalar_one_or_none.return_value = retail_point
    session = AsyncMock()
    session.execute.return_value = result
    repository = PostgresRetailPointRepository(session)

    details = await repository.get_details_by_id(retail_point_id)

    assert details is not None
    assert details.retail_point.id == retail_point_id
    assert details.orders[0].id == order.id
    assert details.debts[0].id == debt.id
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_details_by_id_not_found():
    result = MagicMock()
    result.unique.return_value.scalar_one_or_none.return_value = None
    session = AsyncMock()
    session.execute.return_value = result
    repository = PostgresRetailPointRepository(session)

    details = await repository.get_details_by_id(uuid4())

    assert details is None
