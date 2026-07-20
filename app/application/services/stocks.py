from uuid import UUID

from app.api.v1.schemas.stocks import StockOperationRequest, StockCreateRequest
from app.application.interfaces.uow import IUnitOfWork
from app.domain.entities.stocks import Stock, StockTransaction
from app.domain.enums import (
    StockTransactionType,
    TransactionActorType,
    StockReferenceType,
)


class StockService:

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def _validate(
        self,
        warehouse_id: UUID,
        product_id: UUID,
    ) -> None:
        warehouse = await self._uow.warehouses.get_by_id(warehouse_id)
        if warehouse is None:
            raise ValueError(f"Warehouse with ID {warehouse_id} not found")

        if not warehouse.is_active:
            raise ValueError("Warehouse is inactive")

        product = await self._uow.products.get_by_id(product_id)
        if product is None:
            raise ValueError(f"Product with ID {product_id} not found")

        if not product.is_active:
            raise ValueError("Product is inactive")

    async def _get_stock_for_update(
        self,
        warehouse_id: UUID,
        product_id: UUID,
    ) -> Stock:
        stock = await self._uow.stocks.get_for_update(warehouse_id,product_id)
        if stock is None:
            raise ValueError(f"Stock for warehouse {warehouse_id} and product {product_id} not found")

        return stock

    async def _create_transaction(
        self,
        *,
        stock: Stock,
        quantity_delta: int,
        transaction_type: StockTransactionType,
        actor_type: TransactionActorType,
        created_by_id: UUID | None,
        reference_type: StockReferenceType,
        reference_id: UUID | None,
    ) -> None:
        transaction = StockTransaction(
            warehouse_id=stock.warehouse_id,
            product_id=stock.product_id,
            quantity_delta=quantity_delta,
            transaction_type=transaction_type,
            actor_type=actor_type,
            created_by_id=created_by_id,
            reference_type=reference_type,
            reference_id=reference_id,
        )

        await self._uow.stock_transactions.add(transaction)

    async def create_stock(self, dto: StockCreateRequest) -> Stock:
        await self._validate(dto.warehouse_id, dto.product_id)

        exists = await self._uow.stocks.get(
            dto.warehouse_id,
            dto.product_id,
        )
        if exists:
            raise ValueError("Stock already exists")

        stock = Stock(
            warehouse_id=dto.warehouse_id,
            product_id=dto.product_id,
        )

        await self._uow.stocks.add(stock)
        await self._uow.commit()

        return stock

    async def add_stock(self, dto: StockOperationRequest) -> Stock:
        await self._validate(
            dto.warehouse_id,
            dto.product_id,
        )

        stock = await self._get_stock_for_update(
            dto.warehouse_id,
            dto.product_id,
        )

        stock.increase(dto.quantity)

        await self._uow.stocks.update(stock)
        await self._create_transaction(
            stock=stock,
            quantity_delta=dto.quantity,
            transaction_type=StockTransactionType.RECEIPT,
            actor_type=dto.actor_type,
            created_by_id=dto.created_by_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )

        await self._uow.commit()

        return stock

    async def reserve_stock(self, dto: StockOperationRequest) -> Stock:
        stock = await self._get_stock_for_update(
            dto.warehouse_id,
            dto.product_id,
        )

        stock.reserve(dto.quantity)

        await self._uow.stocks.update(stock)
        await self._create_transaction(
            stock=stock,
            quantity_delta=0,
            transaction_type=StockTransactionType.RESERVATION,
            actor_type=dto.actor_type,
            created_by_id=dto.created_by_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )

        await self._uow.commit()

        return stock

    async def release_reservation(self, dto: StockOperationRequest) -> Stock:
        stock = await self._get_stock_for_update(
            dto.warehouse_id,
            dto.product_id,
        )

        stock.release_reservation(dto.quantity)

        await self._uow.stocks.update(stock)
        await self._create_transaction(
            stock=stock,
            quantity_delta=0,
            transaction_type=StockTransactionType.CANCEL_RESERVATION,
            actor_type=dto.actor_type,
            created_by_id=dto.created_by_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )

        await self._uow.commit()

        return stock

    async def confirm_sale(self, dto: StockOperationRequest,) -> Stock:
        stock = await self._get_stock_for_update(
            dto.warehouse_id,
            dto.product_id,
        )

        stock.sell(dto.quantity)

        await self._uow.stocks.update(stock)
        await self._create_transaction(
            stock=stock,
            quantity_delta=-dto.quantity,
            transaction_type=StockTransactionType.SALE,
            actor_type=dto.actor_type,
            created_by_id=dto.created_by_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )

        await self._uow.commit()

        return stock

    async def write_off(self, dto: StockOperationRequest) -> Stock:
        stock = await self._get_stock_for_update(
            dto.warehouse_id,
            dto.product_id,
        )

        stock.write_off(dto.quantity)

        await self._uow.stocks.update(stock)
        await self._create_transaction(
            stock=stock,
            quantity_delta=-dto.quantity,
            transaction_type=StockTransactionType.WRITEOFF,
            actor_type=dto.actor_type,
            created_by_id=dto.created_by_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )

        await self._uow.commit()

        return stock

    async def return_stock(self, dto: StockOperationRequest) -> Stock:
        stock = await self._get_stock_for_update(
            dto.warehouse_id,
            dto.product_id,
        )

        stock.return_product(dto.quantity)

        await self._uow.stocks.update(stock)
        await self._create_transaction(
            stock=stock,
            quantity_delta=dto.quantity,
            transaction_type=StockTransactionType.RETURN,
            actor_type=dto.actor_type,
            created_by_id=dto.created_by_id,
            reference_type=dto.reference_type,
            reference_id=dto.reference_id,
        )

        await self._uow.commit()

        return stock