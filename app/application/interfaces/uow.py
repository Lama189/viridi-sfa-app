from app.application.interfaces.categories import ICategoryRepository
from app.application.interfaces.products import IProductRepository
from app.application.interfaces.retail_points import IRetailPointRepository
from app.application.interfaces.users import IUserRepository
from app.application.interfaces.warehouses import IWarehouseRepository


class IUnitOfWork:
    warehouses: IWarehouseRepository
    categories: ICategoryRepository
    products: IProductRepository
    retail_points: IRetailPointRepository
    users: IUserRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...