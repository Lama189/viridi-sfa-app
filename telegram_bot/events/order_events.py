import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class OrderCreatedEvent:
    order_id: UUID
    retail_point_id: UUID
    created_by_id: UUID
    warehouse_id: UUID | None = None
    event_type: str = "order.created"


def deserialize_event(body: bytes, target_type: type[Any] | None = None) -> Any:
    data = json.loads(body.decode("utf-8"))

    if target_type is OrderCreatedEvent or (
        isinstance(data, dict)
        and ("order_id" in data and "retail_point_id" in data)
    ):
        return OrderCreatedEvent(
            order_id=UUID(data["order_id"]) if isinstance(data["order_id"], str) else data["order_id"],
            retail_point_id=UUID(data["retail_point_id"]) if isinstance(data["retail_point_id"], str) else data["retail_point_id"],
            created_by_id=UUID(data["created_by_id"]) if isinstance(data["created_by_id"], str) else data["created_by_id"],
            warehouse_id=UUID(data["warehouse_id"]) if data.get("warehouse_id") else None,
            event_type=data.get("event_type", "order.created"),
        )

    return data
