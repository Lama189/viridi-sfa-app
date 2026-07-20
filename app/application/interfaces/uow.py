from app.application.interfaces.repos.categories import ICategoryRepository
from app.application.interfaces.repos.clients import IClientRepository
from app.application.interfaces.repos.employees import IEmployeeRepository
from app.application.interfaces.repos.order_items import IOrderItemRepository
from app.application.interfaces.repos.orders import IOrderRepository
from app.application.interfaces.repos.products import IProductRepository
from app.application.interfaces.repos.retail_points import IRetailPointRepository
from app.application.interfaces.repos.stocks import IStockRepository
from app.application.interfaces.repos.stocks_transactions import IStockTransactionRepository
from app.application.interfaces.repos.warehouses import IWarehouseRepository


class IUnitOfWork:
    warehouses: IWarehouseRepository
    categories: ICategoryRepository
    products: IProductRepository
    retail_points: IRetailPointRepository
    clients: IClientRepository
    employees: IEmployeeRepository
    stocks: IStockRepository
    stock_transactions: IStockTransactionRepository
    orders: IOrderRepository
    order_items: IOrderItemRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...