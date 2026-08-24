from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from app.application.dto.dashboard import DailyReportDTO
from app.application.interfaces.services.dashboard import (
    EmployeeDashboard,
    IDashboardService,
)
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import VisitPlanNotFoundError


class DashboardService(IDashboardService):
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def get_employee_dashboard(
        self,
        employee_id: UUID,
    ) -> EmployeeDashboard:
        today = date.today()

        plan = await self._uow.visit_plans.get_by_employee_and_date(employee_id, today)
        if plan is None:
            raise VisitPlanNotFoundError()

        total_points = await self._uow.visit_plan_items.count_by_plan_id(plan.id)
        completed_points = await self._uow.visits.count_completed_by_plan(
            plan.id, employee_id
        )

        remaining_points = total_points - completed_points

        if total_points == 0:
            completion_percentage = Decimal(0)
        else:
            completion_percentage = (
                Decimal(completed_points) / Decimal(total_points)
            ) * Decimal(100)

        (
            orders_count,
            orders_amount,
        ) = await self._uow.orders.get_statistics_by_employee_and_date(
            employee_id, today
        )

        debts_count = await self._uow.visit_debts.count_by_employee_and_date(
            employee_id, today
        )

        return EmployeeDashboard(
            total_points=total_points,
            completed_points=completed_points,
            remaining_points=remaining_points,
            completion_percentage=completion_percentage,
            orders_count=orders_count,
            orders_amount=orders_amount,
            debts_count=debts_count,
        )

    async def get_agent_daily_report(
        self,
        agent_id: UUID | None,
        date_from: datetime,
        date_to: datetime,
    ) -> DailyReportDTO:
        return await self._uow.sales_reports.get_agent_daily_report(
            agent_id,
            date_from,
            date_to,
        )
