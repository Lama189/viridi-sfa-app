from uuid import UUID

from app.api.v1.schemas.inventory import WarehouseCreate, WarehouseUpdate
from app.application.interfaces.uow import IUnitOfWork
from app.core.observability.metrics import warehouse_operations_total
from app.domain.entities.inventory import Warehouse


class WarehousesService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_warehouse(self, dto: WarehouseCreate) -> Warehouse:
        if await self._uow.warehouses.exists_by(name=dto.name):
            raise ValueError(f"Warehouse name {dto.name} already exists")

        warehouse = Warehouse(name=dto.name, address=dto.address)

        await self._uow.warehouses.add(warehouse)
        await self._uow.commit()
        warehouse_operations_total.labels(action="create").inc()
        return warehouse

    async def get_by_id(self, warehouse_id: UUID) -> Warehouse | None:
        return await self._uow.warehouses.get_by_id(warehouse_id)

    async def get_all_warehouses(self, only_active: bool = True) -> list[Warehouse]:
        return await self._uow.warehouses.list_all(only_active)

    async def update_warehouse(
        self, warehouse_id: UUID, dto: WarehouseUpdate
    ) -> Warehouse:
        warehouse = await self._uow.warehouses.get_by_id(warehouse_id)
        if not warehouse:
            raise ValueError(f"Warehouse {warehouse_id} not found")

        if dto.name is not None:
            warehouse.name = dto.name
        if dto.address is not None:
            warehouse.address = dto.address
        if dto.is_active is not None:
            warehouse.is_active = bool(dto.is_active)

        await self._uow.warehouses.update(warehouse)
        warehouse_operations_total.labels(action="update").inc()
        return warehouse
