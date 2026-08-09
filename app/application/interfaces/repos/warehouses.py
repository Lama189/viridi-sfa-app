from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.inventory import Warehouse


class IWarehouseRepository(ABC):
    @abstractmethod
    async def add(self, warehouse: Warehouse) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, warehouse_id: UUID) -> Warehouse | None:
        raise NotImplementedError

    @abstractmethod
    async def exists_by(self, **kwargs) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list(self, is_active: bool = True) -> list[Warehouse]:
        raise NotImplementedError

    @abstractmethod
    async def list_all(self, only_active: bool = True) -> list[Warehouse]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, warehouse: Warehouse) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, warehouse: Warehouse) -> None:
        raise NotImplementedError
