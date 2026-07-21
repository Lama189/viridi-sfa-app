from types import TracebackType
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.postgres.database import async_session_maker
from app.application.interfaces.uow import IUnitOfWork

from app.infrastructure.postgres.repos.categories import PostgresCategoriesRepository
from app.infrastructure.postgres.repos.clients import PostgresClientRepository
from app.infrastructure.postgres.repos.employees import PostgresEmployeeRepository
from app.infrastructure.postgres.repos.order_items import PostgresOrderItemRepository
from app.infrastructure.postgres.repos.orders import PostgresOrderRepository
from app.infrastructure.postgres.repos.products import PostgresProductsRepository
from app.infrastructure.postgres.repos.invite_codes import PostgresInviteCodeRepository
from app.infrastructure.postgres.repos.retail_point_members import PostgresRetailPointMemberRepository
from app.infrastructure.postgres.repos.retail_points import PostgresRetailPointRepository
from app.infrastructure.postgres.repos.stocks import PostgresStocksRepository
from app.infrastructure.postgres.repos.stock_transactions import PostgresStockTransactionRepository
from app.infrastructure.postgres.repos.warehouses import PostgresWarehousesRepository


class PostgresUnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession | None = None):
        self._session = session

    async def __aenter__(self) -> "PostgresUnitOfWork":
        if self._session is None:
            self._session = async_session_maker()

        self.warehouses = PostgresWarehousesRepository(self._session)
        self.categories = PostgresCategoriesRepository(self._session)
        self.products = PostgresProductsRepository(self._session)
        self.retail_points = PostgresRetailPointRepository(self._session)
        self.retail_point_members = PostgresRetailPointMemberRepository(self._session)
        self.invite_codes = PostgresInviteCodeRepository(self._session)
        self.clients = PostgresClientRepository(self._session)
        self.employees = PostgresEmployeeRepository(self._session)
        self.stocks = PostgresStocksRepository(self._session)
        self.stock_transactions = PostgresStockTransactionRepository(self._session)
        self.orders = PostgresOrderRepository(self._session)
        self.order_items = PostgresOrderItemRepository(self._session)

        return self
    
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.rollback()
        finally:
            if self._session:
                await self._session.close()

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()
