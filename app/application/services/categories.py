from uuid import UUID

from app.application.dto.categories import CategoryCreateDTO, CategoryUpdateDTO
from app.application.interfaces.uow import IUnitOfWork
from app.core.observability.metrics import category_operations_total
from app.domain.entities.inventory import Category


class CategoriesService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_category(self, dto: CategoryCreateDTO) -> Category:
        if await self._uow.categories.exists_by(name=dto.name):
            raise ValueError(f"Category name '{dto.name}' already exists")

        category = Category(name=dto.name)

        await self._uow.categories.add(category)
        await self._uow.commit()
        category_operations_total.labels(action="create").inc()
        return category

    async def get_by_id(self, category_id: UUID) -> Category | None:
        return await self._uow.categories.get_by_id(category_id)

    async def get_all_categories(self, only_active: bool = True) -> list[Category]:
        return await self._uow.categories.list_all(only_active)

    async def update_category(self, category_id: UUID, dto: CategoryUpdateDTO) -> Category:
        category = await self._uow.categories.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        if dto.name is not None:
            category.name = dto.name
        if dto.is_active is not None:
            category.is_active = bool(dto.is_active)

        await self._uow.categories.update(category)
        await self._uow.commit()
        category_operations_total.labels(action="update").inc()
        return category

    async def delete_category(self, category_id: UUID) -> None:
        category = await self._uow.categories.get_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        await self._uow.categories.delete(category)
        await self._uow.commit()
        category_operations_total.labels(action="delete").inc()
