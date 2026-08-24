from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.application.interfaces.repos.orders import IOrderRepository
from app.domain.entities.orders import (
    Order,
    OrderItem,
    ProductShort,
    RetailPointShort,
    UserShort,
    WarehouseShort,
)
from app.domain.enums import OrderStatus
from app.infrastructure.postgres.models.order_items import (
    OrderItem as OrderItemModel,
)
from app.infrastructure.postgres.models.orders import Order as OrderModel
from app.infrastructure.postgres.models.visit_plans import (
    VisitPlan as VisitPlanModel,
)
from app.infrastructure.postgres.models.visits import Visit as VisitModel


class PostgresOrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _hydrated_options(self):
        return (
            joinedload(OrderModel.retail_point),
            joinedload(OrderModel.warehouse),
            joinedload(OrderModel.created_by),
            joinedload(OrderModel.planned_visit).joinedload(VisitPlanModel.employee),
            selectinload(OrderModel.items).joinedload(OrderItemModel.product),
        )

    async def add(self, order: Order) -> None:
        model = self._to_model(order)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, order_id: UUID) -> Order | None:
        return await self.get_by_id_hydrated(order_id)

    async def get_by_id_hydrated(self, order_id: UUID) -> Order | None:
        result = await self._session.execute(
            select(OrderModel)
            .options(*self._hydrated_options())
            .where(OrderModel.id == order_id)
        )

        model = result.unique().scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def list(
        self,
        statuses: list[OrderStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Order]:
        stmt = select(OrderModel).options(*self._hydrated_options())

        if statuses:
            stmt = stmt.where(OrderModel.status.in_(statuses))

        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.unique().scalars().all()]

    async def list_by_client(
        self,
        client_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        stmt = (
            select(OrderModel)
            .options(*self._hydrated_options())
            .where(OrderModel.created_by_id == client_id)
        )
        if statuses:
            stmt = stmt.where(OrderModel.status.in_(statuses))

        result = await self._session.execute(stmt)

        return [self._to_domain(m) for m in result.unique().scalars().all()]

    async def list_by_retail_point(
        self,
        retail_point_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        stmt = (
            select(OrderModel)
            .options(*self._hydrated_options())
            .where(OrderModel.retail_point_id == retail_point_id)
        )
        if statuses:
            stmt = stmt.where(OrderModel.status.in_(statuses))

        result = await self._session.execute(stmt)

        return [self._to_domain(m) for m in result.unique().scalars().all()]

    async def list_by_retail_points(
        self,
        retail_point_ids: list[UUID],
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        if not retail_point_ids:
            return []

        stmt = (
            select(OrderModel)
            .options(*self._hydrated_options())
            .where(OrderModel.retail_point_id.in_(retail_point_ids))
        )
        if statuses:
            stmt = stmt.where(OrderModel.status.in_(statuses))

        result = await self._session.execute(stmt)

        return [self._to_domain(m) for m in result.unique().scalars().all()]

    async def list_by_planned_visit(
        self,
        planned_visit_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        stmt = (
            select(OrderModel)
            .options(*self._hydrated_options())
            .where(OrderModel.planned_visit_id == planned_visit_id)
        )
        if statuses:
            stmt = stmt.where(OrderModel.status.in_(statuses))

        result = await self._session.execute(stmt)

        return [self._to_domain(m) for m in result.unique().scalars().all()]

    async def list_by_source_visit(
        self,
        source_visit_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        stmt = (
            select(OrderModel)
            .options(*self._hydrated_options())
            .where(OrderModel.source_visit_id == source_visit_id)
        )
        if statuses:
            stmt = stmt.where(OrderModel.status.in_(statuses))

        result = await self._session.execute(stmt)

        return [self._to_domain(m) for m in result.unique().scalars().all()]

    async def list_by_actual_visit(
        self,
        actual_visit_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        stmt = (
            select(OrderModel)
            .options(*self._hydrated_options())
            .where(OrderModel.actual_visit_id == actual_visit_id)
        )
        if statuses:
            stmt = stmt.where(OrderModel.status.in_(statuses))

        result = await self._session.execute(stmt)

        return [self._to_domain(m) for m in result.unique().scalars().all()]

    async def update(self, order: Order) -> None:
        await self._session.execute(
            update(OrderModel)
            .where(OrderModel.id == order.id)
            .values(
                status=order.status,
                total_amount=order.total_amount,
                total_volume=order.total_volume,
                source_visit_id=order.source_visit_id,
                planned_visit_id=order.planned_visit_id,
                actual_visit_id=order.actual_visit_id,
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
            .join(VisitModel, OrderModel.actual_visit_id == VisitModel.id)
            .where(
                VisitModel.employee_id == employee_id,
                func.date(VisitModel.started_at) == target_date,
            )
        )

        result = await self._session.execute(stmt)
        count, amount = result.one()
        return count or 0, Decimal(str(amount or "0.00"))

    async def get_counts_by_status(
        self,
        employee_id: UUID | None = None,
    ) -> dict[OrderStatus, int]:
        stmt = select(OrderModel.status, func.count(OrderModel.id)).group_by(
            OrderModel.status
        )

        result = await self._session.execute(stmt)

        counts: dict[OrderStatus, int] = {status: 0 for status in OrderStatus}
        for status, count in result.all():
            if status in counts:
                counts[status] = count

        return counts

    def _to_domain(self, model: OrderModel) -> Order:
        items = []
        for item in getattr(model, "items", []) or []:
            prod = getattr(item, "product", None)
            product_short = (
                ProductShort(
                    id=prod.id,
                    name=prod.name,
                    code=getattr(prod, "code", None),
                    unit_of_measure=getattr(prod, "unit_of_measure", None),
                )
                if prod is not None
                else None
            )
            items.append(
                OrderItem(
                    order_id=item.order_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_at_order=item.price_at_order,
                    total_volume=item.total_volume,
                    id=item.id,
                    product_name=prod.name if prod is not None else None,
                    product=product_short,
                )
            )

        rp = getattr(model, "retail_point", None)
        retail_point_short = (
            RetailPointShort(
                id=rp.id,
                name=rp.name,
                address=rp.address,
            )
            if rp is not None
            else None
        )

        wh = getattr(model, "warehouse", None)
        warehouse_short = (
            WarehouseShort(
                id=wh.id,
                name=wh.name,
            )
            if wh is not None
            else None
        )

        cb = getattr(model, "created_by", None)
        user_short = (
            UserShort(
                id=cb.id,
                full_name=cb.full_name,
            )
            if cb is not None
            else None
        )

        pv = getattr(model, "planned_visit", None)
        planned_delivery_date = pv.plan_date if pv is not None else None
        delivery_agent_name = (
            pv.employee.full_name
            if pv is not None and getattr(pv, "employee", None) is not None
            else None
        )

        return Order(
            warehouse_id=model.warehouse_id,
            created_by_id=model.created_by_id,
            retail_point_id=model.retail_point_id,
            id=model.id,
            source_visit_id=getattr(model, "source_visit_id", None),
            planned_visit_id=model.planned_visit_id,
            planned_delivery_date=planned_delivery_date,
            delivery_agent_name=delivery_agent_name,
            actual_visit_id=model.actual_visit_id,
            status=model.status,
            total_amount=model.total_amount,
            total_volume=model.total_volume,
            created_at=getattr(model, "created_at", None) or datetime.now(UTC),
            updated_at=getattr(model, "updated_at", None) or datetime.now(UTC),
            items=items,
            retail_point=retail_point_short,
            warehouse=warehouse_short,
            created_by=user_short,
        )

    def _to_model(self, order: Order) -> OrderModel:
        return OrderModel(
            id=order.id,
            warehouse_id=order.warehouse_id,
            created_by_id=order.created_by_id,
            retail_point_id=order.retail_point_id,
            source_visit_id=order.source_visit_id,
            planned_visit_id=order.planned_visit_id,
            actual_visit_id=order.actual_visit_id,
            status=order.status,
            total_amount=order.total_amount,
            total_volume=order.total_volume,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
