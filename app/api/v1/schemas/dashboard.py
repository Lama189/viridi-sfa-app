from decimal import Decimal
from pydantic import BaseModel


class EmployeeDashboardResponse(BaseModel):
    total_points: int
    completed_points: int
    remaining_points: int
    completion_percentage: Decimal

    orders_count: int
    orders_amount: Decimal

    debts_count: int

    model_config = {
        "from_attributes": True,
    }
