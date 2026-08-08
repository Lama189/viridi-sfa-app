from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.stocks_transactions import (
    IStockTransactionRepository,
)
from app.domain.entities.stocks import StockTransaction
from app.infrastructure.postgres.models.stock_transactions import (
    StockTransaction as StockTransactionModel,
)


class PostgresStockTransactionRepository(IStockTransactionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, transaction: StockTransaction) -> None:
        model = self._to_model(transaction)
        self._session.add(model)
        await self._session.flush()

    async def list_by_reference(self, reference_id: UUID) -> list[StockTransaction]:
        result = await self._session.execute(
            select(StockTransactionModel).where(
                StockTransactionModel.reference_id == reference_id
            )
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_product(self, product_id: UUID) -> list[StockTransaction]:
        result = await self._session.execute(
            select(StockTransactionModel).where(
                StockTransactionModel.product_id == product_id
            )
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_warehouse(self, warehouse_id: UUID) -> list[StockTransaction]:
        result = await self._session.execute(
            select(StockTransactionModel)
            .where(StockTransactionModel.warehouse_id == warehouse_id)
            .order_by(StockTransactionModel.created_at.desc())
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_all(self) -> list[StockTransaction]:
        result = await self._session.execute(
            select(StockTransactionModel).order_by(
                StockTransactionModel.created_at.desc()
            )
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    def _to_domain(self, model: StockTransactionModel) -> StockTransaction:
        return StockTransaction(
            id=model.id,
            warehouse_id=model.warehouse_id,
            product_id=model.product_id,
            quantity_delta=model.quantity_delta,
            transaction_type=model.transaction_type,
            reference_type=model.reference_type,
            reference_id=model.reference_id,
            actor_type=model.actor_type,
            created_by_id=model.created_by_id,
            created_at=model.created_at,
        )

    def _to_model(self, transaction: StockTransaction) -> StockTransactionModel:
        return StockTransactionModel(
            id=transaction.id,
            warehouse_id=transaction.warehouse_id,
            product_id=transaction.product_id,
            quantity_delta=transaction.quantity_delta,
            transaction_type=transaction.transaction_type,
            reference_type=transaction.reference_type,
            reference_id=transaction.reference_id,
            actor_type=transaction.actor_type,
            created_by_id=transaction.created_by_id,
        )
