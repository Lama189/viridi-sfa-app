from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.dependencies import allow_all_staff, get_current_employee, get_dashboard_service
from app.api.v1.schemas.dashboard import DailyReportDTO, EmployeeDashboardResponse
from app.application.services.dashboard import DashboardService
from app.domain.entities.auth import AuthenticatedEmployee


router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get(
    path="",
    response_model=EmployeeDashboardResponse,
)
async def get_dashboard(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
):
    dashboard = await service.get_employee_dashboard(employee.id)
    return EmployeeDashboardResponse(
        total_points=dashboard.total_points,
        completed_points=dashboard.completed_points,
        remaining_points=dashboard.remaining_points,
        completion_percentage=dashboard.completion_percentage,
        orders_count=dashboard.orders_count,
        orders_amount=dashboard.orders_amount,
        debts_count=dashboard.debts_count,
    )


@router.get(
    path="/daily-report",
    response_model=DailyReportDTO,
)
async def get_daily_report(
    date_from: datetime,
    date_to: datetime,
    employee: Annotated[AuthenticatedEmployee, Depends(allow_all_staff)],
    service: Annotated[DashboardService, Depends(get_dashboard_service)],
):
    return await service.get_agent_daily_report(
        employee.id,
        date_from,
        date_to,
    )
