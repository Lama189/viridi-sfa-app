from dataclasses import dataclass, field
from datetime import date
from uuid import UUID, uuid4

from app.domain.entities.visit_plan_items import VisitPlanItem
from app.domain.enums import VisitPlanStatus, Weekday


@dataclass(slots=True)
class VisitPlan:
    employee_id: UUID
    plan_date: date

    id: UUID = field(default_factory=uuid4)
    status: VisitPlanStatus = VisitPlanStatus.PLANNED

    items: list[VisitPlanItem] = field(default_factory=list)

    @property
    def weekday(self) -> Weekday:
        return Weekday(self.plan_date.weekday())

    def add_item(self, item: VisitPlanItem) -> None:
        if item.visit_plan_id != self.id:
            raise ValueError("Visit plan item belongs to another visit plan")

        if any(existing.order == item.order for existing in self.items):
            raise ValueError("Duplicate visit plan item order")

        self.items.append(item)
