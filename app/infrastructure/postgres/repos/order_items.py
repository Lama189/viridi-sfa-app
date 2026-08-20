from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.interfaces.repos.order_items import IOrderItemRepository
from app.domain.entities.orders import OrderItem
from app.infrastructure.postgres.models.order_items import OrderItem as OrderItemModel


class PostgresOrderItemRepository(IOrderItemRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, item: OrderItem) -> None:
        model = self._to_model(item)
        self._session.add(model)
        await self._session.flush()

    async def list_by_order(self, order_id: UUID) -> list[OrderItem]:
        result = await self._session.execute(
            select(OrderItemModel)
            .options(selectinload(OrderItemModel.product))
            .where(OrderItemModel.order_id == order_id)
        )

        return [self._to_domain(m) for m in result.scalars().all()]

    async def delete_by_order(self, order_id: UUID) -> None:
        await self._session.execute(
            sa_delete(OrderItemModel).where(OrderItemModel.order_id == order_id)
        )
        await self._session.flush()

    def _to_domain(self, model: OrderItemModel) -> OrderItem:
        return OrderItem(
            id=model.id,
            order_id=model.order_id,
            product_id=model.product_id,
            quantity=model.quantity,
            price_at_order=model.price_at_order,
            total_volume=model.total_volume,
            product_name=model.product.name
            if getattr(model, "product", None) is not None
            else None,
        )

    def _to_model(self, item: OrderItem) -> OrderItemModel:
        return OrderItemModel(
            id=item.id,
            order_id=item.order_id,
            product_id=item.product_id,
            quantity=item.quantity,
            price_at_order=item.price_at_order,
            total_volume=item.total_volume,
        )
