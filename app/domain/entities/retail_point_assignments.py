from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(slots=True)
class RetailPointAssignment:
    retail_point_id: UUID
    employee_id: UUID

    id: UUID = field(default_factory=uuid4)

    def change_employee(self, employee_id: UUID) -> None:
        if self.employee_id == employee_id:
            raise ValueError("Employee is already assigned to this retail point.")

        self.employee_id = employee_id

    def belongs_to(self, retail_point_id: UUID) -> bool:
        return self.retail_point_id == retail_point_id