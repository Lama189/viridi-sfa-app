from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.dashboard import EmployeeDashboard


class IDashboardService(ABC):

    @abstractmethod
    async def get_employee_dashboard(
        self,
        employee_id: UUID,
    ) -> EmployeeDashboard:
        raise NotImplementedError
