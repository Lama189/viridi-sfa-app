from app.application.interfaces.repos.categories import ICategoryRepository
from app.application.interfaces.repos.clients import IClientRepository
from app.application.interfaces.repos.employees import IEmployeeRepository
from app.application.interfaces.repos.invite_codes import IInviteCodeRepository
from app.application.interfaces.repos.media_objects import IMediaObjectRepository
from app.application.interfaces.repos.order_items import IOrderItemRepository
from app.application.interfaces.repos.orders import IOrderRepository
from app.application.interfaces.repos.products import IProductRepository
from app.application.interfaces.repos.retail_point_assignments import IRetailPointAssignmentRepository
from app.application.interfaces.repos.retail_point_members import IRetailPointMemberRepository
from app.application.interfaces.repos.retail_points import IRetailPointRepository
from app.application.interfaces.repos.stocks import IStockRepository
from app.application.interfaces.repos.stocks_transactions import IStockTransactionRepository
from app.application.interfaces.repos.visit_debts import IVisitDebtRepository
from app.application.interfaces.repos.visit_media import IVisitMediaRepository
from app.application.interfaces.repos.visits import IVisitRepository
from app.application.interfaces.repos.visit_plans import IVisitPlanRepository
from app.application.interfaces.repos.visit_plan_items import IVisitPlanItemRepository
from app.application.interfaces.repos.warehouses import IWarehouseRepository
from app.application.interfaces.repos.visit_schedule_rules import IVisitScheduleRuleRepository


class IUnitOfWork:
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
    media_objects: IMediaObjectRepository
    visits: IVisitRepository
    visit_media: IVisitMediaRepository
    visit_debts: IVisitDebtRepository
    visit_plans: IVisitPlanRepository
    visit_plan_items: IVisitPlanItemRepository
    visit_schedule_rules: IVisitScheduleRuleRepository

    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...