from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.orders import IOrderRepository
from app.domain.entities.orders import Order
from app.infrastructure.postgres.models.orders import Order as OrderModel
from app.infrastructure.postgres.models.visits import Visit as VisitModel


class PostgresOrderRepository(IOrderRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, order: Order) -> None:
        model = self._to_model(order)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, order_id: UUID) -> Order | None:
        result = await self._session.execute(
            select(OrderModel).where(OrderModel.id == order_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list_by_client(self, client_id: UUID) -> list[Order]:
        result = await self._session.execute(
            select(OrderModel).where(OrderModel.created_by_id == client_id)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def list_by_retail_point(self, retail_point_id: UUID) -> list[Order]:
        result = await self._session.execute(
            select(OrderModel).where(OrderModel.retail_point_id == retail_point_id)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, order: Order) -> None:
        await self._session.execute(
            update(OrderModel)
            .where(OrderModel.id == order.id)
            .values(
                status=order.status,
                total_amount=order.total_amount,
                total_volume=order.total_volume,
                visit_id=order.visit_id,
            )
        )
        await self._session.flush()

    async def delete(self, order: Order) -> None:
        await self._session.execute(
            sa_delete(OrderModel).where(OrderModel.id == order.id)
        )
        await self._session.flush()

    async def get_statistics_by_employee_and_date(
        self,
        employee_id: UUID,
        target_date: date,
    ) -> tuple[int, Decimal]:
        stmt = (
            select(
                func.count(OrderModel.id),
                func.coalesce(func.sum(OrderModel.total_amount), Decimal("0.00")),
            )
            .select_from(OrderModel)
            .join(VisitModel, OrderModel.visit_id == VisitModel.id)
            .where(
                VisitModel.employee_id == employee_id,
                func.date(VisitModel.started_at) == target_date,
            )
        )

        result = await self._session.execute(stmt)
        count, amount = result.one()
        return count or 0, Decimal(str(amount or "0.00"))


    def _to_domain(self, model: OrderModel) -> Order:
        return Order(
            warehouse_id=model.warehouse_id,
            created_by_id=model.created_by_id,
            retail_point_id=model.retail_point_id,
            id=model.id,
            visit_id=model.visit_id,
            status=model.status,
            total_amount=model.total_amount,
            total_volume=model.total_volume,
        )

    def _to_model(self, order: Order) -> OrderModel:
        return OrderModel(
            id=order.id,
            warehouse_id=order.warehouse_id,
            created_by_id=order.created_by_id,
            retail_point_id=order.retail_point_id,
            visit_id=order.visit_id,
            status=order.status,
            total_amount=order.total_amount,
            total_volume=order.total_volume,
        )
