from dataclasses import dataclass
from decimal import Decimal


@dataclass
class EmployeeDashboard:
    total_points: int
    completed_points: int
    remaining_points: int
    completion_percentage: Decimal

    orders_count: int
    orders_amount: Decimal

    debts_count: int