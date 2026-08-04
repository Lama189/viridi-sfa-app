from decimal import Decimal
from uuid import UUID

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


class CategoryReportDTO(BaseModel):
    category_id: UUID
    category_name: str
    quantity_pcs: int
    volume_boxes: Decimal
    total_amount: Decimal


class DailyReportDTO(BaseModel):
    total_amount: Decimal
    acb_count: int
    total_quantity_pcs: int
    total_volume_boxes: Decimal
    categories: list[CategoryReportDTO]

    model_config = {
        "from_attributes": True,
    }
