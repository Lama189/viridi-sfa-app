from uuid import UUID

from app.application.dto.products import ProductCreateDTO, ProductUpdateDTO
from app.application.interfaces.uow import IUnitOfWork
from app.core.observability.metrics import product_operations_total
from app.domain.entities.inventory import Product


class ProductsService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_product(self, dto: ProductCreateDTO) -> Product:
        category = await self._uow.categories.get_by_id(dto.category_id)
        if not category:
            raise ValueError(f"Category with ID {dto.category_id} not found")

        if not category.is_active:
            raise ValueError("You cannot add a product to an inactive category.")

        if await self._uow.products.exists_by(name=dto.name):
            raise ValueError(f"A product named '{dto.name}' already exists")

        product = Product(
            name=dto.name,
            price=dto.price,
            category_id=dto.category_id,
            volume=dto.volume,
            weight=dto.weight,
            items_in_box=dto.items_in_box,
        )

        await self._uow.products.add(product)
        await self._uow.commit()
        product_operations_total.labels(action="create").inc()
        return product

    async def get_by_id(self, product_id: UUID) -> Product | None:
        return await self._uow.products.get_by_id(product_id)

    async def get_all_products(self, only_active: bool = True) -> list[Product]:
        return await self._uow.products.list_all(only_active)

    async def update_product(self, product_id: UUID, dto: ProductUpdateDTO) -> Product:
        product = await self._uow.products.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        if dto.category_id is not None:
            category = await self._uow.categories.get_by_id(dto.category_id)
            if not category:
                raise ValueError(f"Category with ID {dto.category_id} not found")
            if not category.is_active:
                raise ValueError("You cannot assign a product to an inactive category.")
            product.category_id = dto.category_id

        if dto.name is not None:
            product.name = dto.name
        if dto.price is not None:
            product.price = dto.price
        if dto.volume is not None:
            product.volume = dto.volume
        if dto.weight is not None:
            product.weight = dto.weight
        if dto.items_in_box is not None:
            product.items_in_box = dto.items_in_box
        if dto.is_active is not None:
            product.is_active = bool(dto.is_active)

        await self._uow.products.update(product)
        await self._uow.commit()
        product_operations_total.labels(action="update").inc()
        return product

    async def delete_product(self, product_id: UUID) -> None:
        product = await self._uow.products.get_by_id(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        await self._uow.products.delete(product)
        await self._uow.commit()
        product_operations_total.labels(action="delete").inc()
