from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from app.application.interfaces.repos.categories import ICategoryRepository
from app.application.interfaces.repos.clients import IClientRepository
from app.application.interfaces.repos.employees import IEmployeeRepository
from app.application.interfaces.repos.invite_codes import IInviteCodeRepository
from app.application.interfaces.repos.media_objects import IMediaObjectRepository
from app.application.interfaces.repos.order_items import IOrderItemRepository
from app.application.interfaces.repos.orders import IOrderRepository
from app.application.interfaces.repos.outbox import IOutboxRepository
from app.application.interfaces.repos.products import IProductRepository
from app.application.interfaces.repos.retail_point_assignments import (
    IRetailPointAssignmentRepository,
)
from app.application.interfaces.repos.retail_point_members import (
    IRetailPointMemberRepository,
)
from app.application.interfaces.repos.retail_points import IRetailPointRepository
from app.application.interfaces.repos.sales_reports import ISalesReportRepository
from app.application.interfaces.repos.stocks import IStockRepository
from app.application.interfaces.repos.stocks_transactions import (
    IStockTransactionRepository,
)
from app.application.interfaces.repos.visit_debts import IVisitDebtRepository
from app.application.interfaces.repos.visit_media import IVisitMediaRepository
from app.application.interfaces.repos.visit_plan_items import IVisitPlanItemRepository
from app.application.interfaces.repos.visit_plans import IVisitPlanRepository
from app.application.interfaces.repos.visit_schedule_rules import (
    IVisitScheduleRuleRepository,
)
from app.application.interfaces.repos.visits import IVisitRepository
from app.application.interfaces.repos.warehouses import IWarehouseRepository


class IUnitOfWork(ABC):
    warehouses: IWarehouseRepository
    categories: ICategoryRepository
    products: IProductRepository
    retail_points: IRetailPointRepository
    retail_point_members: IRetailPointMemberRepository
    retail_point_assignments: IRetailPointAssignmentRepository
    invite_codes: IInviteCodeRepository
    clients: IClientRepository
    employees: IEmployeeRepository
    stocks: IStockRepository
    stock_transactions: IStockTransactionRepository
    orders: IOrderRepository
    order_items: IOrderItemRepository
    sales_reports: ISalesReportRepository
    media_objects: IMediaObjectRepository
    visits: IVisitRepository
    visit_media: IVisitMediaRepository
    visit_debts: IVisitDebtRepository
    visit_plans: IVisitPlanRepository
    visit_plan_items: IVisitPlanItemRepository
    visit_schedule_rules: IVisitScheduleRuleRepository
    outbox: IOutboxRepository

    @abstractmethod
    async def __aenter__(self) -> Self:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None: 
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
