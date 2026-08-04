from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.stocks import StockTransaction
from app.domain.enums import (
    StockReferenceType,
    StockTransactionType,
    TransactionActorType,
)
from app.infrastructure.postgres.repos.stock_transactions import (
    PostgresStockTransactionRepository,
)


@pytest.mark.asyncio
async def test_stock_transaction_repo_add_list(session: AsyncSession):
    repo = PostgresStockTransactionRepository(session)
    wh_id = uuid4()
    prod_id = uuid4()
    ref_id = uuid4()
    actor_id = uuid4()

    tx = StockTransaction(
        warehouse_id=wh_id,
        product_id=prod_id,
        quantity_delta=50,
        transaction_type=StockTransactionType.RECEIPT,
        reference_type=StockReferenceType.RECEIPT,
        reference_id=ref_id,
        actor_type=TransactionActorType.EMPLOYEE,
        created_by_id=actor_id,
    )

    await repo.add(tx)
    await session.commit()

    by_ref = await repo.list_by_reference(ref_id)
    assert len(by_ref) == 1
    assert by_ref[0].id == tx.id

    by_prod = await repo.list_by_product(prod_id)
    assert len(by_prod) == 1

    by_wh = await repo.list_by_warehouse(wh_id)
    assert len(by_wh) == 1
