from uuid import UUID

from app.core.extensions import UserNotFoundError
from app.domain.entities.orders import Order, OrderItem
from app.domain.entities.inventory import Product
from app.application.interfaces.uow import IUnitOfWork
from app.application.services.stocks import IStockService
from app.api.v1.schemas.orders import CreateOrderRequest, OrderItemCreateRequest
from app.api.v1.schemas.stocks import StockOperationRequest
from app.domain.enums import (
    TransactionActorType,
    StockReferenceType,
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
            raise UserNotFoundError()
        
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if retail_point_id is None:
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


    async def create(self, client_id: UUID, dto: CreateOrderRequest) -> Order:
        await self._validate(dto.warehouse_id, client_id, dto.retail_point_id)

        products = await self._get_products(dto.items)
        order = Order(
            warehouse_id=dto.warehouse_id,
            created_by_id=client_id,
            retail_point_id=dto.retail_point_id
        )

        order_items: list[OrderItem] = []

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

            await self._stocks.reserve_stock(
                StockOperationRequest(
                    warehouse_id=dto.warehouse_id,
                    product_id=product.id,
                    quantity=item.quantity,
                    actor_type=TransactionActorType.CLIENT,
                    created_by_id=client_id,
                    reference_type=StockReferenceType.ORDER,
                    reference_id=order.id,
                )
            )
            
        await self._uow.orders.add(order)
        for item in order_items:
            await self._uow.order_items.add(item)
        
        await self._uow.commit()

        return order

