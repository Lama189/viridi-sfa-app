from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.api.v1.schemas.dashboard import DailyReportDTO
from app.domain.entities.dashboard import EmployeeDashboard


class IDashboardService(ABC):
    @abstractmethod
    async def get_employee_dashboard(
        self,
        employee_id: UUID,
    ) -> EmployeeDashboard:
        raise NotImplementedError

    @abstractmethod
    async def get_agent_daily_report(
        self,
        agent_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> DailyReportDTO:
        raise NotImplementedError
