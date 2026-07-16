from app.application.interfaces.categories import ICategoryRepository
from app.application.interfaces.warehouses import IWarehouseRepository


class IUnitOfWork:
    warehouses: IWarehouseRepository
    categories: ICategoryRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...