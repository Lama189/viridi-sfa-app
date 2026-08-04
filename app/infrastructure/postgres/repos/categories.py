from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.categories import ICategoryRepository
from app.domain.entities.inventory import Category
from app.infrastructure.postgres.models.categories import Category as CategoryModel


class PostgresCategoriesRepository(ICategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, category: Category) -> None:
        model = self._to_model(category)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, category_id: UUID) -> Category | None:
        result = await self._session.execute(
            select(CategoryModel).where(CategoryModel.id == category_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(CategoryModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_all(self, only_active: bool = True) -> list[Category]:
        stmt = select(CategoryModel)
        if only_active:
            stmt = stmt.where(CategoryModel.is_active.is_(True))

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, category: Category) -> None:
        await self._session.execute(
            update(CategoryModel)
            .where(CategoryModel.id == category.id)
            .values(
                name=category.name,
                is_active=category.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, category: Category) -> None:
        await self._session.execute(
            sa_delete(CategoryModel).where(CategoryModel.id == category.id)
        )
        await self._session.flush()

    def _to_domain(self, model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name=model.name,
            is_active=model.is_active,
        )

    def _to_model(self, category: Category) -> CategoryModel:
        return CategoryModel(
            id=category.id,
            name=category.name,
            is_active=category.is_active,
        )
