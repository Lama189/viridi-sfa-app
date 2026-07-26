from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.domain.enums import VisitPlanItemStatus


@dataclass(slots=True)
class VisitPlanItem:
    visit_plan_id: UUID
    retail_point_id: UUID
    order: int

    id: UUID = field(default_factory=uuid4)
    status: VisitPlanItemStatus = VisitPlanItemStatus.PENDING

    def __post_init__(self) -> None:
        if self.order <= 0:
            raise ValueError("Order cannot be negative")
