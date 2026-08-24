from datetime import date
from uuid import UUID

from app.application.dto.orders import (
    OrderCreateDTO,
    OrderItemCreateDTO,
)
from app.application.dto.stocks import (
    StockBatchItemDTO,
    StockBatchOperationDTO,
)
from app.application.interfaces.services.delivery_assignments import (
    IDeliveryAssignmentService,
)
from app.application.interfaces.services.stocks import IStockService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import UserNotActiveError, UserNotFoundError
from app.domain.entities.inventory import Product
from app.domain.entities.orders import (
    Order,
    OrderItem,
    ProductShort,
    RetailPointShort,
    UserShort,
    WarehouseShort,
)
from app.domain.entities.outbox_messages import OutboxMessage
from app.domain.enums import (
    AggregateType,
    OrderEventType,
    OrderStatus,
    StockReferenceType,
    TransactionActorType,
)


class OrdersService:
    def __init__(
        self,
        uow: IUnitOfWork,
        stocks: IStockService,
        delivery_assignment_service: IDeliveryAssignmentService | None = None,
    ) -> None:
        self._uow = uow
        self._stocks = stocks
        self._delivery_assignment_service = delivery_assignment_service

    async def _validate(
        self,
        warehouse_id: UUID,
        created_by_id: UUID,
        retail_point_id: UUID,
        source_visit_id: UUID | None = None,
        actual_visit_id: UUID | None = None,
    ) -> None:
        warehouse = await self._uow.warehouses.get_by_id(warehouse_id)
        if warehouse is None:
            raise ValueError(f"Warehouse with ID {warehouse_id} not found")

        if not warehouse.is_active:
            raise ValueError("Warehouse is inactive")

        client = await self._uow.clients.get_by_id(created_by_id)
        employee = (
            await self._uow.employees.get_by_id(created_by_id)
            if client is None
            else None
        )

        if client is None and employee is None:
            raise UserNotFoundError()

        if client and not client.is_active:
            raise UserNotActiveError()

        if employee and not employee.is_active:
            raise UserNotActiveError()

        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if retail_point is None:
            raise ValueError(f"Retail Point with ID {retail_point_id} not found")

        if retail_point and not retail_point.is_active:
            raise ValueError("Retail Point is inactive")

        if source_visit_id:
            visit = await self._uow.visits.get_by_id(source_visit_id)
            if visit is None:
                raise ValueError(f"Visit with ID {source_visit_id} not found")
            if visit.retail_point_id != retail_point_id:
                raise ValueError("Visit does not match retail point")

        if actual_visit_id:
            visit = await self._uow.visits.get_by_id(actual_visit_id)
            if visit is None:
                raise ValueError(f"Visit with ID {actual_visit_id} not found")
            if visit.retail_point_id != retail_point_id:
                raise ValueError("Visit does not match retail point")

    async def _get_products(
        self,
        items: list[OrderItemCreateDTO],
    ) -> dict[UUID, Product]:
        product_ids = [item.product_id for item in items]

        products = await self._uow.products.list_by_ids(product_ids)

        if len(products) != len(set(product_ids)):
            raise ValueError("Some products not found")

        for product in products:
            if not product.is_active:
                raise ValueError(f"Product {product.name} is inactive")

        return {product.id: product for product in products}

    async def get_by_id(self, order_id: UUID) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")
        return order

    async def list_orders(
        self,
        statuses: list[OrderStatus] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Order]:
        return await self._uow.orders.list(
            statuses=statuses, limit=limit, offset=offset
        )

    async def list_by_client(
        self,
        client_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        return await self._uow.orders.list_by_client(client_id, statuses=statuses)

    async def list_by_client_retail_point(
        self,
        client_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        memberships = await self._uow.retail_point_members.get_by_client_id(client_id)
        if not memberships:
            return []

        retail_point_ids = [m.retail_point_id for m in memberships]
        return await self._uow.orders.list_by_retail_points(
            retail_point_ids, statuses=statuses
        )

    async def list_by_retail_point(
        self,
        retail_point_id: UUID,
        statuses: list[OrderStatus] | None = None,
    ) -> list[Order]:
        return await self._uow.orders.list_by_retail_point(
            retail_point_id, statuses=statuses
        )

    async def get_counts_by_status(
        self,
        employee_id: UUID | None = None,
    ) -> dict[OrderStatus, int]:
        return await self._uow.orders.get_counts_by_status(employee_id=employee_id)

    async def create(self, creator_id: UUID, dto: OrderCreateDTO) -> Order:
        await self._validate(
            dto.warehouse_id,
            creator_id,
            dto.retail_point_id,
            dto.source_visit_id,
            dto.actual_visit_id,
        )

        warehouse = await self._uow.warehouses.get_by_id(dto.warehouse_id)
        client = await self._uow.clients.get_by_id(creator_id)
        employee = (
            await self._uow.employees.get_by_id(creator_id) if client is None else None
        )
        retail_point = await self._uow.retail_points.get_by_id(dto.retail_point_id)
        products = await self._get_products(dto.items)

        creator_name = (
            client.full_name if client else (employee.full_name if employee else "")
        )

        order = Order(
            warehouse_id=dto.warehouse_id,
            created_by_id=creator_id,
            retail_point_id=dto.retail_point_id,
            source_visit_id=dto.source_visit_id,
            planned_visit_id=dto.planned_visit_id,
            actual_visit_id=dto.actual_visit_id,
            retail_point=RetailPointShort(
                id=retail_point.id,
                name=retail_point.name,
                address=retail_point.address,
            )
            if retail_point
            else None,
            warehouse=WarehouseShort(
                id=warehouse.id,
                name=warehouse.name,
            )
            if warehouse
            else None,
            created_by=UserShort(
                id=creator_id,
                full_name=creator_name,
            ),
        )

        order_items: list[OrderItem] = []
        batch_items: list[StockBatchItemDTO] = []

        for item in dto.items:
            product = products[item.product_id]

            order_item = OrderItem(
                order.id,
                item.product_id,
                quantity=item.quantity,
                price_at_order=product.price,
                total_volume=product.volume * item.quantity,
                product_name=product.name,
                product=ProductShort(
                    id=product.id,
                    name=product.name,
                    code=getattr(product, "code", None),
                    unit_of_measure=getattr(product, "unit_of_measure", None),
                ),
            )

            order.add_item(order_item)
            order_items.append(order_item)
            batch_items.append(
                StockBatchItemDTO(
                    product_id=product.id,
                    quantity=item.quantity,
                )
            )

        await self._stocks.reserve_stocks_batch(
            StockBatchOperationDTO(
                warehouse_id=dto.warehouse_id,
                items=batch_items,
                actor_type=TransactionActorType.CLIENT
                if client
                else TransactionActorType.EMPLOYEE,
                created_by_id=creator_id,
                reference_type=StockReferenceType.ORDER,
                reference_id=order.id,
            )
        )

        await self._uow.orders.add(order)
        for item in order_items:
            await self._uow.order_items.add(item)

        event = OutboxMessage.create(
            event_type=OrderEventType.CREATED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.CREATED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(creator_id),
            },
        )

        await self._uow.outbox.add(event)

        await self._uow.commit()

        return order

    async def confirm(self, order_id: UUID) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        if order.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order with ID {order_id}")

        order.confirm()

        if self._delivery_assignment_service:
            await self._delivery_assignment_service.assign_order_to_next_visit(order)

        await self._uow.orders.update(order)

        event = OutboxMessage.create(
            event_type=OrderEventType.CONFIRMED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.CONFIRMED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
                "planned_visit_id": str(order.planned_visit_id)
                if order.planned_visit_id
                else None,
            },
        )
        await self._uow.outbox.add(event)

        await self._uow.commit()

        return order

    async def cancel(self, order_id: UUID) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        if order.status == OrderStatus.DELIVERED:
            raise ValueError(f"Cannot cancel order in status {order.status}")

        batch_items = [
            StockBatchItemDTO(
                product_id=order_item.product_id,
                quantity=order_item.quantity,
            )
            for order_item in order.items
        ]

        await self._stocks.release_reservations_batch(
            StockBatchOperationDTO(
                warehouse_id=order.warehouse_id,
                items=batch_items,
                actor_type=TransactionActorType.CLIENT,
                created_by_id=order.created_by_id,
                reference_type=StockReferenceType.ORDER,
                reference_id=order.id,
            )
        )

        order.cancel()
        if order.planned_visit_id is not None:
            order.planned_visit_id = None

        event = OutboxMessage.create(
            event_type=OrderEventType.CANCELLED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.CANCELLED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
            },
        )
        await self._uow.outbox.add(event)

        await self._uow.orders.update(order)
        await self._uow.commit()

        return order

    async def start_assembly(
        self,
        order_id: UUID,
        employee_id: UUID | None = None,
    ) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        order.start_assembly()

        await self._uow.orders.update(order)

        event = OutboxMessage.create(
            event_type=OrderEventType.ASSEMBLY_STARTED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.ASSEMBLY_STARTED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
                "employee_id": str(employee_id) if employee_id is not None else None,
            },
        )

        await self._uow.outbox.add(event)
        await self._uow.commit()

        return order

    async def complete_assembly(
        self,
        order_id: UUID,
        employee_id: UUID | None = None,
    ) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        order.complete_assembly()

        await self._uow.orders.update(order)

        event = OutboxMessage.create(
            event_type=OrderEventType.ASSEMBLED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.ASSEMBLED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
                "employee_id": str(employee_id) if employee_id is not None else None,
            },
        )

        await self._uow.outbox.add(event)
        await self._uow.commit()

        return order

    async def load_order(
        self,
        order_id: UUID,
        employee_id: UUID | None = None,
    ) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        order.load()

        await self._uow.orders.update(order)

        event = OutboxMessage.create(
            event_type=OrderEventType.LOADED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.LOADED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
                "employee_id": str(employee_id) if employee_id is not None else None,
                "planned_visit_id": str(order.planned_visit_id)
                if order.planned_visit_id
                else None,
            },
        )

        await self._uow.outbox.add(event)
        await self._uow.commit()

        return order

    async def load_today_orders(
        self,
        employee_id: UUID,
    ) -> list[Order]:
        today_plan = await self._uow.visit_plans.get_by_employee_and_date(
            employee_id, date.today()
        )
        if not today_plan:
            return []

        orders = await self._uow.orders.list_by_planned_visit(
            planned_visit_id=today_plan.id,
            statuses=[OrderStatus.ASSEMBLED],
        )

        for order in orders:
            order.load()
            await self._uow.orders.update(order)

            event = OutboxMessage.create(
                event_type=OrderEventType.LOADED,
                aggregate_type=AggregateType.ORDER,
                aggregate_id=order.id,
                payload={
                    "event_type": OrderEventType.LOADED,
                    "order_id": str(order.id),
                    "warehouse_id": str(order.warehouse_id),
                    "retail_point_id": str(order.retail_point_id),
                    "created_by_id": str(order.created_by_id),
                    "employee_id": str(employee_id),
                    "planned_visit_id": str(order.planned_visit_id)
                    if order.planned_visit_id
                    else None,
                },
            )
            await self._uow.outbox.add(event)

        await self._uow.commit()
        return orders

    async def ship(
        self,
        order_id: UUID,
        employee_id: UUID | None = None,
    ) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        order.ship()

        await self._uow.orders.update(order)

        event = OutboxMessage.create(
            event_type=OrderEventType.TAKEN_BY_AGENT,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.TAKEN_BY_AGENT,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
                "employee_id": str(employee_id) if employee_id is not None else None,
            },
        )

        await self._uow.outbox.add(event)
        await self._uow.commit()

        return order

    async def deliver(
        self,
        order_id: UUID,
        employee_id: UUID | None = None,
        visit_id: UUID | None = None,
    ) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        if visit_id is None and employee_id is not None:
            active_visits = await self._uow.visits.list_by_employee(
                employee_id, active=True, limit=1
            )
            if (
                active_visits
                and active_visits[0].retail_point_id == order.retail_point_id
            ):
                visit_id = active_visits[0].id

        batch_items = [
            StockBatchItemDTO(
                product_id=order_item.product_id,
                quantity=order_item.quantity,
            )
            for order_item in order.items
        ]

        await self._stocks.confirm_sales_batch(
            StockBatchOperationDTO(
                warehouse_id=order.warehouse_id,
                items=batch_items,
                actor_type=TransactionActorType.EMPLOYEE
                if employee_id
                else TransactionActorType.CLIENT,
                created_by_id=employee_id or order.created_by_id,
                reference_type=StockReferenceType.ORDER,
                reference_id=order.id,
            )
        )

        order.deliver(actual_visit_id=visit_id)

        if order.planned_visit_id:
            plan = await self._uow.visit_plans.get_by_id(order.planned_visit_id)
            if plan:
                if visit_id:
                    visit = await self._uow.visits.get_by_id(visit_id)
                    if visit and (
                        visit.employee_id != plan.employee_id
                        or (
                            visit.started_at
                            and visit.started_at.date() != plan.plan_date
                        )
                    ):
                        order.planned_visit_id = None
                else:
                    order.planned_visit_id = None

        await self._uow.orders.update(order)

        event = OutboxMessage.create(
            event_type=OrderEventType.DELIVERED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.DELIVERED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
                "employee_id": str(employee_id) if employee_id is not None else None,
                "actual_visit_id": str(order.actual_visit_id)
                if order.actual_visit_id
                else None,
                "planned_visit_id": str(order.planned_visit_id)
                if order.planned_visit_id
                else None,
            },
        )

        await self._uow.outbox.add(event)
        await self._uow.commit()

        return order
