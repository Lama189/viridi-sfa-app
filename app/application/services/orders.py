from uuid import UUID

from app.api.v1.schemas.orders import CreateOrderRequest, OrderItemCreateRequest
from app.application.dto.stocks import (
    StockBatchItemDTO,
    StockBatchOperationDTO,
)
from app.application.interfaces.services.stocks import IStockService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import UserNotActiveError, UserNotFoundError
from app.domain.entities.inventory import Product
from app.domain.entities.orders import Order, OrderItem
from app.domain.entities.outbox_messages import OutboxMessage
from app.domain.enums import (
    AggregateType,
    OrderEventType,
    OrderStatus,
    StockReferenceType,
    TransactionActorType,
)


class OrdersService:
    def __init__(self, uow: IUnitOfWork, stocks: IStockService) -> None:
        self._uow = uow
        self._stocks = stocks

    async def _validate(
        self,
        warehouse_id: UUID,
        created_by_id: UUID,
        retail_point_id: UUID,
    ) -> None:
        warehouse = await self._uow.warehouses.get_by_id(warehouse_id)
        if warehouse is None:
            raise ValueError(f"Warehouse with ID {warehouse_id} not found")

        if not warehouse.is_active:
            raise ValueError("Warehouse is inactive")

        client = await self._uow.clients.get_by_id(created_by_id)
        if client is None:
            raise UserNotFoundError()

        if not client.is_active:
            raise UserNotActiveError()

        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if retail_point is None:
            raise ValueError(f"Retail Point with ID {retail_point_id} not found")

        if retail_point and not retail_point.is_active:
            raise ValueError("Retail Point is inactive")

    async def _get_products(
        self,
        items: list[OrderItemCreateRequest],
    ) -> dict[UUID, Product]:
        product_ids = [item.product_id for item in items]

        products = await self._uow.products.list_by_ids(product_ids)

        if len(products) != len(set(product_ids)):
            found_ids = {product.id for product in products}
            missing = set(product_ids) - found_ids
            raise ValueError(f"Products not found: {missing}")

        for product in products:
            if not product.is_active:
                raise ValueError(f"Product '{product.name}' is inactive")

        return {product.id: product for product in products}

    async def get_by_id(self, order_id: UUID) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")
        return order

    async def list_by_client(self, client_id: UUID) -> list[Order]:
        return await self._uow.orders.list_by_client(client_id)

    async def list_by_retail_point(self, retail_point_id: UUID) -> list[Order]:
        return await self._uow.orders.list_by_retail_point(retail_point_id)

    async def create(self, client_id: UUID, dto: CreateOrderRequest) -> Order:
        await self._validate(dto.warehouse_id, client_id, dto.retail_point_id)

        products = await self._get_products(dto.items)
        order = Order(
            warehouse_id=dto.warehouse_id,
            created_by_id=client_id,
            retail_point_id=dto.retail_point_id,
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
                actor_type=TransactionActorType.CLIENT,
                created_by_id=client_id,
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
                "created_by_id": str(client_id),
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
                actor_type=TransactionActorType.CLIENT,
                created_by_id=order.created_by_id,
                reference_type=StockReferenceType.ORDER,
                reference_id=order.id,
            )
        )

        order.confirm()

        await self._uow.orders.update(order)
        await self._uow.commit()

        return order

    async def cancel(self, order_id: UUID) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        if order.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
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
    ) -> Order:
        order = await self._uow.orders.get_by_id(order_id)
        if order is None:
            raise ValueError(f"Order with ID {order_id} not found")

        order.deliver()

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
            },
        )

        await self._uow.outbox.add(event)
        await self._uow.commit()

        return order
