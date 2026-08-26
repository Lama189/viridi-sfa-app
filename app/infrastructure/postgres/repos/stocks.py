from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.application.dto.categories import CategoryDTO
from app.application.dto.stocks import ProductWithStockDTO, StockSummaryDTO
from app.application.dto.warehouses import WarehouseShortDTO
from app.application.interfaces.repos.stocks import IStockRepository
from app.domain.entities.stocks import Stock
from app.infrastructure.postgres.models.products import Product as ProductModel
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

    async def get_for_update(
        self, warehouse_id: UUID, product_id: UUID
    ) -> Stock | None:
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
        result = await self._session.execute(
            select(StockModel)
            .where(
                StockModel.warehouse_id == warehouse_id,
                StockModel.product_id.in_(product_ids),
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

    async def get_stocks_by_warehouse(
        self, warehouse_id: UUID
    ) -> list[ProductWithStockDTO]:
        stmt = (
            select(StockModel)
            .where(StockModel.warehouse_id == warehouse_id)
            .options(
                joinedload(StockModel.warehouse),
                joinedload(StockModel.product).joinedload(ProductModel.category),
            )
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        inventory: list[ProductWithStockDTO] = []
        for stock in models:
            category_dto = CategoryDTO(
                id=stock.product.category.id,
                name=stock.product.category.name,
                is_active=stock.product.category.is_active,
            )
            stock_summary_dto = StockSummaryDTO(
                warehouse=WarehouseShortDTO(
                    id=stock.warehouse.id,
                    name=stock.warehouse.name,
                ),
                quantity=stock.quantity,
                reserved_quantity=stock.reserved_quantity,
                available_quantity=stock.quantity - stock.reserved_quantity,
                updated_at=getattr(stock, "updated_at", None),
            )
            product_dto = ProductWithStockDTO(
                id=stock.product.id,
                name=stock.product.name,
                price=stock.product.price,
                volume=stock.product.volume,
                weight=stock.product.weight,
                items_in_box=stock.product.items_in_box,
                category=category_dto,
                photo_url=getattr(stock.product, "photo_url", None),
                stock=stock_summary_dto,
            )
            inventory.append(product_dto)
        return inventory

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
