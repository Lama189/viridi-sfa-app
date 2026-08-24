from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID


@dataclass
class EmployeeDashboard:
    total_points: int
    completed_points: int
    remaining_points: int
    completion_percentage: Decimal

    orders_count: int
    orders_amount: Decimal

    debts_count: int


@dataclass
class ProductReport:
    product_id: UUID
    product_name: str
    quantity_pcs: int
    volume_boxes: Decimal
    total_amount: Decimal


@dataclass
class CategoryReport:
    category_id: UUID
    category_name: str
    quantity_pcs: int
    volume_boxes: Decimal
    total_amount: Decimal
    products: list[ProductReport] = field(default_factory=list)


@dataclass
class DailyReport:
    total_amount: Decimal
    acb_count: int
    total_quantity_pcs: int
    total_volume_boxes: Decimal
    categories: list[CategoryReport]
