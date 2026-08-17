from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.application.dto.dashboard import DailyReportDTO


class ISalesReportRepository(ABC):
    @abstractmethod
    async def get_agent_daily_report(
        self,
        agent_id: UUID,
        date_from: datetime,
        date_to: datetime,
    ) -> DailyReportDTO:
        raise NotImplementedError
