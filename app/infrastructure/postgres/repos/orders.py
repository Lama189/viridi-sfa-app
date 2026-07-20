from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.orders import IOrderRepository
from app.domain.entities.orders import Order
from app.infrastructure.postgres.models.orders import Order as OrderModel


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
                updated_at=order.updated_at,
            )
        )
        await self._session.flush()

    async def delete(self, order: Order) -> None:
        await self._session.execute(
            sa_delete(OrderModel).where(OrderModel.id == order.id)
        )
        await self._session.flush()

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
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
