from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.domain.entities.orders import Order
from app.domain.enums import OrderStatus


class IOrderRepository(ABC):
    @abstractmethod
    async def add(self, order: Order) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_hydrated(self, order_id: UUID) -> Order | None:
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        statuses: list[OrderStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_client(
        self,
        client_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_retail_point(
        self,
        retail_point_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_retail_points(
        self,
        retail_point_ids: list[UUID],
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    async def list_by_planned_visit(
        self,
        planned_visit_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        raise NotImplementedError

    @abstractmethod
    async def update(self, order: Order) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, order: Order) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_statistics_by_employee_and_date(
        self,
        employee_id: UUID,
        target_date: date,
    ) -> tuple[int, Decimal]:
        raise NotImplementedError

    @abstractmethod
    async def get_counts_by_status(
        self,
        employee_id: UUID | None = None,
    ) -> dict[OrderStatus, int]:
        raise NotImplementedError
