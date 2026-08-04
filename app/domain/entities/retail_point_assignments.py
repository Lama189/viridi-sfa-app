from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(slots=True)
class RetailPointAssignment:
    retail_point_id: UUID
    employee_id: UUID | None

    id: UUID = field(default_factory=uuid4)

    def assign_employee(
        self,
        employee_id: UUID,
    ) -> None:
        self.employee_id = employee_id

    def remove_employee(self) -> None:
        self.employee_id = None

    @property
    def is_assigned(self) -> bool:
        return self.employee_id is not None
