from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.domain.enums import AggregateType, EventType


@dataclass(slots=True)
class OutboxMessage:
    event_type: EventType
    aggregate_type: AggregateType
    aggregate_id: UUID
    payload: dict[str, Any]

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    processed_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        event_type: EventType,
        aggregate_type: AggregateType,
        aggregate_id: UUID,
        payload: dict[str, Any],
        now: datetime | None = None,
    ) -> "OutboxMessage":
        current_time = now or datetime.now(timezone.utc)
        return cls(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            created_at=current_time,
        )

    def mark_processed(
        self,
        *,
        now: datetime | None = None,
    ) -> None:
        if self.processed_at is not None:
            raise ValueError("Outbox message is already processed")

        self.processed_at = now or datetime.now(timezone.utc)

    @property
    def is_processed(self) -> bool:
        return self.processed_at is not None
