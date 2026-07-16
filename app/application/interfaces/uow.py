from app.application.interfaces.warehouses import IWarehouseRepository


class IUnitOfWork:
    warehouses: IWarehouseRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...