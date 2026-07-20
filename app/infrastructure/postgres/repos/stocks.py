from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.stocks import IStockRepository
from app.domain.entities.stocks import Stock
from app.infrastructure.postgres.models.stocks import Stock as StockModel


class PostgresStocksRepository(IStockRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, stock: Stock) -> None:
        model = self._to_model(stock)
        self._session.add(model)
        await self._session.flush()

    async def get(self, warehouse_id: UUID, product_id: UUID) -> Stock | None:
        result = await self._session.execute(
            select(StockModel).where(
                StockModel.warehouse_id == warehouse_id,
                StockModel.product_id == product_id,
            )
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_for_update(self, warehouse_id: UUID, product_id: UUID) -> Stock | None:
        result = await self._session.execute(
            select(StockModel)
            .where(
                StockModel.warehouse_id == warehouse_id,
                StockModel.product_id == product_id,
            )
            .with_for_update()
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_many_for_update(
        self,
        warehouse_id: UUID,
        product_ids: list[UUID],
    ) -> list[Stock]:
        sorted_ids = sorted(product_ids)

        result = await self._session.execute(
            select(StockModel)
            .where(
                StockModel.warehouse_id == warehouse_id,
                StockModel.product_id.in_(sorted_ids),
            )
            .order_by(StockModel.product_id) 
            .with_for_update()
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(StockModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_by_warehouse(self, warehouse_id: UUID) -> list[Stock]:
        result = await self._session.execute(
            select(StockModel).where(StockModel.warehouse_id == warehouse_id)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, stock: Stock) -> None:
        await self._session.execute(
            update(StockModel)
            .where(
                StockModel.warehouse_id == stock.warehouse_id,
                StockModel.product_id == stock.product_id,
            )
            .values(
                quantity=stock.quantity,
                reserved_quantity=stock.reserved_quantity,
            )
        )
        await self._session.flush()

    async def delete(self, stock: Stock) -> None:
        await self._session.execute(
            sa_delete(StockModel).where(
                StockModel.warehouse_id == stock.warehouse_id,
                StockModel.product_id == stock.product_id,
            )
        )
        await self._session.flush()

    def _to_domain(self, model: StockModel) -> Stock:
        return Stock(
            warehouse_id=model.warehouse_id,
            product_id=model.product_id,
            quantity=model.quantity,
            reserved_quantity=model.reserved_quantity,
        )

    def _to_model(self, stock: Stock) -> StockModel:
        return StockModel(
            warehouse_id=stock.warehouse_id,
            product_id=stock.product_id,
            quantity=stock.quantity,
            reserved_quantity=stock.reserved_quantity,
        )
