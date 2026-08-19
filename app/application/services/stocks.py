from uuid import UUID

from app.application.dto.categories import CategoryDTO
from app.application.dto.stocks import (
    ProductWithStockDTO,
    StockBatchOperationDTO,
    StockCreateDTO,
    StockOperationDTO,
    StockSummaryDTO,
)
from app.application.dto.warehouses import WarehouseShortDTO
from app.application.interfaces.services.stocks import IStockService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import (
    InsufficientReservationError,
    InsufficientReservedStockError,
    InsufficientStockError,
    ProductInactiveError,
    ProductNotFoundError,
    StockAlreadyExistsError,
    StockNotFoundError,
    WarehouseInactiveError,
    WarehouseNotFoundError,
)
from app.core.observability.logging import logger
from app.core.observability.metrics import (
    stock_operation_failures_total,
    stock_operation_units_total,
    stock_operations_total,
)
from app.domain.entities.stocks import Stock, StockTransaction
from app.domain.enums import (
    StockReferenceType,
    StockTransactionType,
    TransactionActorType,
)


class StockService(IStockService):
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    def _map_exception_to_reason(self, exc: Exception) -> str:
        if isinstance(exc, WarehouseNotFoundError):
            return "warehouse_not_found"
        if isinstance(exc, WarehouseInactiveError):
            return "warehouse_inactive"
        if isinstance(exc, ProductNotFoundError):
            return "product_not_found"
        if isinstance(exc, ProductInactiveError):
            return "product_inactive"
        if isinstance(exc, StockNotFoundError):
            return "stock_not_found"
        if isinstance(exc, StockAlreadyExistsError):
            return "stock_already_exists"
        if isinstance(exc, InsufficientStockError):
            return "insufficient_stock"
        if isinstance(exc, InsufficientReservedStockError):
            return "insufficient_reserved_stock"
        if isinstance(exc, InsufficientReservationError):
            return "insufficient_reservation"
        if isinstance(exc, ValueError):
            return "invalid_value"
        return "unexpected_error"

    async def _validate(
        self,
        warehouse_id: UUID,
        product_id: UUID,
    ) -> None:
        warehouse = await self._uow.warehouses.get_by_id(warehouse_id)
        if warehouse is None:
            logger.warning(
                "Warehouse not found for stock operation",
                warehouse_id=str(warehouse_id),
            )
            raise WarehouseNotFoundError(f"Warehouse with ID {warehouse_id} not found")

        if not warehouse.is_active:
            logger.warning(
                "Warehouse is inactive for stock operation",
                warehouse_id=str(warehouse_id),
            )
            raise WarehouseInactiveError("Warehouse is inactive")

        product = await self._uow.products.get_by_id(product_id)
        if product is None:
            logger.warning(
                "Product not found for stock operation",
                product_id=str(product_id),
            )
            raise ProductNotFoundError(f"Product with ID {product_id} not found")

        if not product.is_active:
            logger.warning(
                "Product is inactive for stock operation",
                product_id=str(product_id),
            )
            raise ProductInactiveError("Product is inactive")

    async def _get_stock_for_update(
        self,
        warehouse_id: UUID,
        product_id: UUID,
    ) -> Stock:
        stock = await self._uow.stocks.get_for_update(warehouse_id, product_id)
        if stock is None:
            logger.warning(
                "Stock record not found for update",
                warehouse_id=str(warehouse_id),
                product_id=str(product_id),
            )
            raise StockNotFoundError(
                f"Stock for warehouse {warehouse_id} and product {product_id} not found"
            )

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

    async def create_stock(self, dto: StockCreateDTO) -> Stock:
        try:
            await self._validate(dto.warehouse_id, dto.product_id)

            exists = await self._uow.stocks.get(
                dto.warehouse_id,
                dto.product_id,
            )
            if exists:
                logger.warning(
                    "Stock record already exists",
                    warehouse_id=str(dto.warehouse_id),
                    product_id=str(dto.product_id),
                )
                raise StockAlreadyExistsError("Stock already exists")

            stock = Stock(
                warehouse_id=dto.warehouse_id,
                product_id=dto.product_id,
            )

            await self._uow.stocks.add(stock)

            logger.info(
                "Stock record successfully created",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
            )
            stock_operations_total.labels(operation="create_stock").inc()
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to create stock",
                warehouse_id=str(dto.warehouse_id),
                product_id=str(dto.product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="create_stock", reason=self._map_exception_to_reason(exc)
            ).inc()
            raise

    async def add_stock(self, dto: StockOperationDTO) -> Stock:
        try:
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

            logger.info(
                "Stock successfully increased",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
                new_quantity=stock.quantity,
            )
            stock_operations_total.labels(operation="add_stock").inc()
            stock_operation_units_total.labels(operation="add_stock").inc(dto.quantity)
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to add stock",
                warehouse_id=str(dto.warehouse_id),
                product_id=str(dto.product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="add_stock", reason=self._map_exception_to_reason(exc)
            ).inc()
            raise

    async def reserve_stock(self, dto: StockOperationDTO) -> Stock:
        try:
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

            logger.info(
                "Stock successfully reserved",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
                reserved_quantity=stock.reserved_quantity,
                available_quantity=stock.available_quantity,
            )
            stock_operations_total.labels(operation="reserve_stock").inc()
            stock_operation_units_total.labels(operation="reserve_stock").inc(
                dto.quantity
            )
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to reserve stock",
                warehouse_id=str(dto.warehouse_id),
                product_id=str(dto.product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="reserve_stock", reason=self._map_exception_to_reason(exc)
            ).inc()
            raise

    async def reserve_stocks_batch(self, dto: StockBatchOperationDTO) -> list[Stock]:
        units = sum(item.quantity for item in dto.items) if dto.items else 0
        try:
            if not dto.items:
                logger.info(
                    "Batch reserve requested with empty items list",
                    warehouse_id=str(dto.warehouse_id),
                )
                stock_operations_total.labels(operation="reserve_stocks_batch").inc()
                return []

            product_ids = [item.product_id for item in dto.items]
            stocks = await self._uow.stocks.get_many_for_update(
                dto.warehouse_id, product_ids
            )
            stock_map = {s.product_id: s for s in stocks}

            updated_stocks: list[Stock] = []
            for item in dto.items:
                stock = stock_map.get(item.product_id)
                if stock is None:
                    logger.warning(
                        "Stock record not found during batch reservation",
                        warehouse_id=str(dto.warehouse_id),
                        product_id=str(item.product_id),
                    )
                    raise StockNotFoundError(
                        f"Stock for warehouse {dto.warehouse_id} and product {item.product_id} not found"
                    )

                stock.reserve(item.quantity)
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
                updated_stocks.append(stock)

            logger.info(
                "Stocks batch successfully reserved",
                warehouse_id=str(dto.warehouse_id),
                items_count=len(updated_stocks),
            )
            stock_operations_total.labels(operation="reserve_stocks_batch").inc()
            if units > 0:
                stock_operation_units_total.labels(
                    operation="reserve_stocks_batch"
                ).inc(units)
            return updated_stocks
        
        except Exception as exc:
            logger.error(
                "Failed to reserve stocks batch",
                warehouse_id=str(dto.warehouse_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="reserve_stocks_batch",
                reason=self._map_exception_to_reason(exc),
            ).inc()
            raise

    async def release_reservation(self, dto: StockOperationDTO) -> Stock:
        try:
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

            logger.info(
                "Stock reservation successfully released",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
                reserved_quantity=stock.reserved_quantity,
            )
            stock_operations_total.labels(operation="release_reservation").inc()
            stock_operation_units_total.labels(operation="release_reservation").inc(
                dto.quantity
            )
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to release stock reservation",
                warehouse_id=str(dto.warehouse_id),
                product_id=str(dto.product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="release_reservation",
                reason=self._map_exception_to_reason(exc),
            ).inc()
            raise

    async def release_reservations_batch(
        self, dto: StockBatchOperationDTO
    ) -> list[Stock]:
        units = sum(item.quantity for item in dto.items) if dto.items else 0
        try:
            if not dto.items:
                logger.info(
                    "Batch release reservation requested with empty items list",
                    warehouse_id=str(dto.warehouse_id),
                )
                stock_operations_total.labels(
                    operation="release_reservations_batch"
                ).inc()
                return []

            product_ids = [item.product_id for item in dto.items]
            stocks = await self._uow.stocks.get_many_for_update(
                dto.warehouse_id, product_ids
            )
            stock_map = {s.product_id: s for s in stocks}

            updated_stocks: list[Stock] = []
            for item in dto.items:
                stock = stock_map.get(item.product_id)
                if stock is None:
                    logger.warning(
                        "Stock record not found during batch reservation release",
                        warehouse_id=str(dto.warehouse_id),
                        product_id=str(item.product_id),
                    )
                    raise StockNotFoundError(
                        f"Stock for warehouse {dto.warehouse_id} and product {item.product_id} not found"
                    )

                stock.release_reservation(item.quantity)
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
                updated_stocks.append(stock)

            logger.info(
                "Stock reservations batch successfully released",
                warehouse_id=str(dto.warehouse_id),
                items_count=len(updated_stocks),
            )
            stock_operations_total.labels(operation="release_reservations_batch").inc()
            if units > 0:
                stock_operation_units_total.labels(
                    operation="release_reservations_batch"
                ).inc(units)
            return updated_stocks
        
        except Exception as exc:
            logger.error(
                "Failed to release stock reservations batch",
                warehouse_id=str(dto.warehouse_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="release_reservations_batch",
                reason=self._map_exception_to_reason(exc),
            ).inc()
            raise

    async def confirm_sale(self, dto: StockOperationDTO) -> Stock:
        try:
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

            logger.info(
                "Stock sale successfully confirmed",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
                new_quantity=stock.quantity,
                reserved_quantity=stock.reserved_quantity,
            )
            stock_operations_total.labels(operation="confirm_sale").inc()
            stock_operation_units_total.labels(operation="confirm_sale").inc(
                dto.quantity
            )
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to confirm sale",
                warehouse_id=str(dto.warehouse_id),
                product_id=str(dto.product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="confirm_sale", reason=self._map_exception_to_reason(exc)
            ).inc()
            raise

    async def confirm_sales_batch(self, dto: StockBatchOperationDTO) -> list[Stock]:
        units = sum(item.quantity for item in dto.items) if dto.items else 0
        try:
            if not dto.items:
                logger.info(
                    "Batch confirm sales requested with empty items list",
                    warehouse_id=str(dto.warehouse_id),
                )
                stock_operations_total.labels(operation="confirm_sales_batch").inc()
                return []

            product_ids = [item.product_id for item in dto.items]
            stocks = await self._uow.stocks.get_many_for_update(
                dto.warehouse_id, product_ids
            )
            stock_map = {s.product_id: s for s in stocks}

            updated_stocks: list[Stock] = []
            for item in dto.items:
                stock = stock_map.get(item.product_id)
                if stock is None:
                    logger.warning(
                        "Stock record not found during batch sale confirmation",
                        warehouse_id=str(dto.warehouse_id),
                        product_id=str(item.product_id),
                    )
                    raise StockNotFoundError(
                        f"Stock for warehouse {dto.warehouse_id} and product {item.product_id} not found"
                    )

                stock.sell(item.quantity)
                await self._uow.stocks.update(stock)
                await self._create_transaction(
                    stock=stock,
                    quantity_delta=-item.quantity,
                    transaction_type=StockTransactionType.SALE,
                    actor_type=dto.actor_type,
                    created_by_id=dto.created_by_id,
                    reference_type=dto.reference_type,
                    reference_id=dto.reference_id,
                )
                updated_stocks.append(stock)

            logger.info(
                "Sales batch successfully confirmed",
                warehouse_id=str(dto.warehouse_id),
                items_count=len(updated_stocks),
            )
            stock_operations_total.labels(operation="confirm_sales_batch").inc()
            if units > 0:
                stock_operation_units_total.labels(operation="confirm_sales_batch").inc(
                    units
                )
            return updated_stocks
        
        except Exception as exc:
            logger.error(
                "Failed to confirm sales batch",
                warehouse_id=str(dto.warehouse_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="confirm_sales_batch",
                reason=self._map_exception_to_reason(exc),
            ).inc()
            raise

    async def write_off(self, dto: StockOperationDTO) -> Stock:
        try:
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

            logger.info(
                "Stock successfully written off",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
                new_quantity=stock.quantity,
            )
            stock_operations_total.labels(operation="write_off").inc()
            stock_operation_units_total.labels(operation="write_off").inc(dto.quantity)
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to write off stock",
                warehouse_id=str(dto.warehouse_id),
                product_id=str(dto.product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="write_off", reason=self._map_exception_to_reason(exc)
            ).inc()
            raise

    async def return_stock(self, dto: StockOperationDTO) -> Stock:
        try:
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

            logger.info(
                "Stock successfully returned",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
                new_quantity=stock.quantity,
            )
            stock_operations_total.labels(operation="return_stock").inc()
            stock_operation_units_total.labels(operation="return_stock").inc(
                dto.quantity
            )
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to return stock",
                warehouse_id=str(dto.warehouse_id),
                product_id=str(dto.product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="return_stock", reason=self._map_exception_to_reason(exc)
            ).inc()
            raise

    async def list_transactions(
        self,
        warehouse_id: UUID | None = None,
        product_id: UUID | None = None,
        reference_id: UUID | None = None,
    ) -> list[StockTransaction]:
        if reference_id is not None:
            return await self._uow.stock_transactions.list_by_reference(reference_id)
        if product_id is not None:
            return await self._uow.stock_transactions.list_by_product(product_id)
        if warehouse_id is not None:
            return await self._uow.stock_transactions.list_by_warehouse(warehouse_id)
        return await self._uow.stock_transactions.list_all()

    async def adjust_stock(
        self,
        warehouse_id: UUID,
        product_id: UUID,
        new_quantity: int,
        actor_id: UUID | None = None,
        reference_id: UUID | None = None,
    ) -> Stock:
        try:
            await self._validate(warehouse_id, product_id)
            stock = await self._get_stock_for_update(warehouse_id, product_id)
            delta = stock.adjust(new_quantity)

            await self._uow.stocks.update(stock)
            await self._create_transaction(
                stock=stock,
                quantity_delta=delta,
                transaction_type=StockTransactionType.ADJUSTMENT,
                actor_type=TransactionActorType.EMPLOYEE,
                created_by_id=actor_id,
                reference_type=StockReferenceType.INVENTORY,
                reference_id=reference_id,
            )
            await self._uow.commit()

            logger.info(
                "Stock successfully adjusted",
                warehouse_id=str(stock.warehouse_id),
                product_id=str(stock.product_id),
                new_quantity=stock.quantity,
                delta=delta,
            )
            stock_operations_total.labels(operation="adjust_stock").inc()
            return stock
        
        except Exception as exc:
            logger.error(
                "Failed to adjust stock",
                warehouse_id=str(warehouse_id),
                product_id=str(product_id),
                error=str(exc),
            )
            stock_operation_failures_total.labels(
                operation="adjust_stock", reason=self._map_exception_to_reason(exc)
            ).inc()
            raise

    async def get_warehouse_inventory(
        self, warehouse_id: UUID
    ) -> list[ProductWithStockDTO]:
        stocks = await self._uow.stocks.get_stocks_by_warehouse(warehouse_id)

        result = []
        for stock in stocks:
            category_dto = CategoryDTO(
                id=stock.product.category.id,
                name=stock.product.category.name,
                is_active=stock.product.category.is_active,
            )
            stock_summary_dto = StockSummaryDTO(
                warehouse=WarehouseShortDTO(
                    id=stock.warehouse.id,
                    name=stock.warehouse.name,
                ),
                quantity=stock.quantity,
                reserved_quantity=stock.reserved_quantity,
                available_quantity=stock.quantity - stock.reserved_quantity,
                updated_at=getattr(stock, "updated_at", None),
            )
            product_dto = ProductWithStockDTO(
                id=stock.product.id,
                name=stock.product.name,
                price=stock.product.price,
                volume=stock.product.volume,
                weight=stock.product.weight,
                items_in_box=stock.product.items_in_box,
                category=category_dto,
                photo_url=getattr(stock.product, "photo_url", None),
                stock=stock_summary_dto,
            )
            result.append(product_dto)

        return result
