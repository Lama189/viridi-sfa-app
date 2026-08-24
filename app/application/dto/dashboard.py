from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass(slots=True, frozen=True)
class ProductReportDTO:
    product_id: UUID
    product_name: str
    quantity_pcs: int
    volume_boxes: Decimal
    total_amount: Decimal


@dataclass(slots=True, frozen=True)
class CategoryReportDTO:
    category_id: UUID
    category_name: str
    quantity_pcs: int
    volume_boxes: Decimal
    total_amount: Decimal
    products: list[ProductReportDTO] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class DailyReportDTO:
    total_amount: Decimal
    acb_count: int
    total_quantity_pcs: int
    total_volume_boxes: Decimal
    categories: list[CategoryReportDTO] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class EmployeeDashboardDTO:
    total_points: int
    completed_points: int
    remaining_points: int
    completion_percentage: Decimal
    orders_count: int
    orders_amount: Decimal
    debts_count: int
