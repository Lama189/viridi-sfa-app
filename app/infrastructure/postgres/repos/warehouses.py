from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.warehouses import IWarehouseRepository
from app.domain.entities.inventory import Warehouse
from app.infrastructure.postgres.models.warehouses import Warehouse as WarehouseModel


class PostgresWarehousesRepository(IWarehouseRepository):
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, warehouse: Warehouse) -> None:
        model = self._to_model(warehouse)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, warehouse_id: UUID) -> Warehouse | None:
        result = await self._session.execute(
            select(WarehouseModel).where(WarehouseModel.id == warehouse_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(WarehouseModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_all(self, only_active: bool = True) -> list[Warehouse]:
        stmt = select(WarehouseModel)
        if only_active:
            stmt = stmt.where(WarehouseModel.is_active.is_(True))
            
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, warehouse: Warehouse) -> None:
        await self._session.execute(
            update(WarehouseModel)
            .where(WarehouseModel.id == warehouse.id)
            .values(
                name=warehouse.name,
                address=warehouse.address,
                is_active=warehouse.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, warehouse: Warehouse) -> None:
        await self._session.execute(
            sa_delete(WarehouseModel).where(WarehouseModel.id == warehouse.id)
        )
        await self._session.flush()

    def _to_domain(self, model: WarehouseModel) -> Warehouse:
        return Warehouse(
            id=model.id,
            name=model.name,
            address=model.address,
            is_active=model.is_active,
        )

    def _to_model(self, warehouse: Warehouse) -> WarehouseModel:
        return WarehouseModel(
            id=warehouse.id,
            name=warehouse.name,
            address=warehouse.address,
            is_active=warehouse.is_active,
        )
