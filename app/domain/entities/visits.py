from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from app.domain.enums import VisitStatus

if TYPE_CHECKING:
    from app.domain.entities.retail_points import RetailPoint
    from app.domain.entities.visit_debts import VisitDebt
    from app.domain.entities.visit_media import VisitMedia


@dataclass(slots=True)
class Visit:
    employee_id: UUID
    retail_point_id: UUID

    started_at: datetime | None = None
    finished_at: datetime | None = None

    id: UUID = field(default_factory=uuid4)
    status: VisitStatus = VisitStatus.IN_PROGRESS

    def start(self) -> None:
        if self.started_at is not None:
            raise ValueError("Visit has already been started.")

        if self.status != VisitStatus.IN_PROGRESS:
            raise ValueError("Visit cannot be started")

        self.started_at = datetime.now(UTC)

    def finish(self) -> None:
        if self.started_at is None:
            raise ValueError("Visit has not been started.")

        if self.finished_at is not None:
            raise ValueError("Visit has already been finished.")

        if self.status != VisitStatus.IN_PROGRESS:
            raise ValueError("Visit cannot be finished.")

        self.status = VisitStatus.COMPLETED
        self.finished_at = datetime.now(UTC)

    def cancel(self) -> None:
        if self.status == VisitStatus.COMPLETED:
            raise ValueError("Completed visit cannot be cancelled.")

        if self.status == VisitStatus.CANCELLED:
            raise ValueError("Visit has already been cancelled.")

        self.status = VisitStatus.CANCELLED
        self.finished_at = datetime.now(UTC)

    @property
    def is_active(self) -> bool:
        return (
            self.status == VisitStatus.IN_PROGRESS
            and self.started_at is not None
            and self.finished_at is None
        )

    def can_attach_media(self) -> bool:
        return True

    def can_add_debt(self) -> bool:
        return self.is_active


@dataclass(slots=True)
class VisitDetails:
    visit: Visit
    retail_point: "RetailPoint"
    debts: list["VisitDebt"] = field(default_factory=list)
    media: list["VisitMedia"] = field(default_factory=list)
