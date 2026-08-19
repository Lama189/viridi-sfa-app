from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.interfaces.uow import IUnitOfWork
from app.infrastructure.postgres.database import async_session_maker
from app.infrastructure.postgres.repos.categories import PostgresCategoriesRepository
from app.infrastructure.postgres.repos.clients import PostgresClientRepository
from app.infrastructure.postgres.repos.employees import PostgresEmployeeRepository
from app.infrastructure.postgres.repos.invite_codes import PostgresInviteCodeRepository
from app.infrastructure.postgres.repos.media_objects import (
    PostgresMediaObjectRepository,
)
from app.infrastructure.postgres.repos.notifications import (
    PostgresNotificationRepository,
)
from app.infrastructure.postgres.repos.order_items import PostgresOrderItemRepository
from app.infrastructure.postgres.repos.orders import PostgresOrderRepository
from app.infrastructure.postgres.repos.outbox import PostgresOutboxRepository
from app.infrastructure.postgres.repos.products import PostgresProductsRepository
from app.infrastructure.postgres.repos.retail_point_assignments import (
    PostgresRetailPointAssignmentRepository,
)
from app.infrastructure.postgres.repos.retail_point_members import (
    PostgresRetailPointMemberRepository,
)
from app.infrastructure.postgres.repos.retail_points import (
    PostgresRetailPointRepository,
)
from app.infrastructure.postgres.repos.sales_reports import SalesReportRepository
from app.infrastructure.postgres.repos.stock_transactions import (
    PostgresStockTransactionRepository,
)
from app.infrastructure.postgres.repos.stocks import PostgresStocksRepository
from app.infrastructure.postgres.repos.visit_debts import PostgresVisitDebtRepository
from app.infrastructure.postgres.repos.visit_media import PostgresVisitMediaRepository
from app.infrastructure.postgres.repos.visit_plan_items import (
    PostgresVisitPlanItemRepository,
)
from app.infrastructure.postgres.repos.visit_plans import PostgresVisitPlanRepository
from app.infrastructure.postgres.repos.visits import PostgresVisitRepository
from app.infrastructure.postgres.repos.visits_schedule_rules import (
    PostgresVisitScheduleRuleRepository,
)
from app.infrastructure.postgres.repos.warehouses import PostgresWarehousesRepository


class PostgresUnitOfWork(IUnitOfWork):
    def __init__(
        self,
        session: AsyncSession | None = None,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
    ):
        self._session = session
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        if self._session is None:
            if self._session_factory is not None:
                self._session = self._session_factory()
            else:
                self._session = async_session_maker()

        self.warehouses = PostgresWarehousesRepository(self._session)
        self.categories = PostgresCategoriesRepository(self._session)
        self.products = PostgresProductsRepository(self._session)
        self.retail_points = PostgresRetailPointRepository(self._session)
        self.retail_point_members = PostgresRetailPointMemberRepository(self._session)
        self.retail_point_assignments = PostgresRetailPointAssignmentRepository(
            self._session
        )
        self.invite_codes = PostgresInviteCodeRepository(self._session)
        self.clients = PostgresClientRepository(self._session)
        self.employees = PostgresEmployeeRepository(self._session)
        self.stocks = PostgresStocksRepository(self._session)
        self.stock_transactions = PostgresStockTransactionRepository(self._session)
        self.orders = PostgresOrderRepository(self._session)
        self.order_items = PostgresOrderItemRepository(self._session)
        self.sales_reports = SalesReportRepository(self._session)
        self.media_objects = PostgresMediaObjectRepository(self._session)
        self.visits = PostgresVisitRepository(self._session)
        self.visit_media = PostgresVisitMediaRepository(self._session)
        self.visit_debts = PostgresVisitDebtRepository(self._session)
        self.visit_plans = PostgresVisitPlanRepository(self._session)
        self.visit_plan_items = PostgresVisitPlanItemRepository(self._session)
        self.visit_schedule_rules = PostgresVisitScheduleRuleRepository(self._session)
        self.notifications = PostgresNotificationRepository(self._session)
        self.outbox = PostgresOutboxRepository(self._session)

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
                self._session = None

    async def commit(self) -> None:
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        if self._session:
            await self._session.rollback()
