from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.products import IProductRepository
from app.domain.entities.inventory import Product
from app.infrastructure.postgres.models.products import Product as ProductModel


class PostgresProductsRepository(IProductRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, product: Product) -> None:
        model = self._to_model(product)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, product_id: UUID) -> Product | None:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None
        
        return self._to_domain(model)

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(ProductModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_all(self, only_active: bool = True) -> list[Product]:
        stmt = select(ProductModel)
        if only_active:
            stmt = stmt.where(ProductModel.is_active.is_(True))
            
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, product: Product) -> None:
        await self._session.execute(
            update(ProductModel)
            .where(ProductModel.id == product.id)
            .values(
                category_id=product.category_id,
                name=product.name,
                price=product.price,
                volume=product.volume,
                weight=product.weight,
                is_active=product.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, product: Product) -> None:
        await self._session.execute(
            sa_delete(ProductModel).where(ProductModel.id == product.id)
        )
        await self._session.flush()

    def _to_domain(self, model: ProductModel) -> Product:
        return Product(
            id=model.id,
            category_id=model.category_id,
            name=model.name,
            price=model.price,
            volume=model.volume,
            weight=model.weight,
            is_active=model.is_active,
        )

    def _to_model(self, product: Product) -> ProductModel:
        return ProductModel(
            id=product.id,
            category_id=product.category_id,
            name=product.name,
            price=product.price,
            volume=product.volume,
            weight=product.weight,
            is_active=product.is_active,
        )
