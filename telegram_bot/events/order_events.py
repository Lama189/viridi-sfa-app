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


@dataclass(slots=True)
class OrderAssemblyStartedEvent:
    order_id: UUID
    retail_point_id: UUID | None = None
    created_by_id: UUID | None = None
    warehouse_id: UUID | None = None
    employee_id: UUID | None = None
    event_type: str = "order.assembly_started"


@dataclass(slots=True)
class OrderAssembledEvent:
    order_id: UUID
    retail_point_id: UUID | None = None
    created_by_id: UUID | None = None
    warehouse_id: UUID | None = None
    employee_id: UUID | None = None
    event_type: str = "order.assembled"


@dataclass(slots=True)
class OrderTakenByAgentEvent:
    order_id: UUID
    retail_point_id: UUID | None = None
    created_by_id: UUID | None = None
    warehouse_id: UUID | None = None
    employee_id: UUID | None = None
    event_type: str = "order.taken_by_agent"


@dataclass(slots=True)
class OrderDeliveredEvent:
    order_id: UUID
    retail_point_id: UUID | None = None
    created_by_id: UUID | None = None
    warehouse_id: UUID | None = None
    employee_id: UUID | None = None
    event_type: str = "order.delivered"


@dataclass(slots=True)
class OrderCancelledEvent:
    order_id: UUID
    retail_point_id: UUID | None = None
    created_by_id: UUID | None = None
    warehouse_id: UUID | None = None
    event_type: str = "order.cancelled"


def deserialize_event(body: bytes, target_type: type[Any] | None = None) -> Any:
    data = json.loads(body.decode("utf-8"))

    if not isinstance(data, dict):
        return data

    event_type = data.get("event_type")

    if target_type is OrderAssemblyStartedEvent or event_type == "order.assembly_started":
        return OrderAssemblyStartedEvent(
            order_id=UUID(data["order_id"])
            if isinstance(data["order_id"], str)
            else data["order_id"],
            retail_point_id=UUID(data["retail_point_id"])
            if data.get("retail_point_id")
            else None,
            created_by_id=UUID(data["created_by_id"])
            if data.get("created_by_id")
            else None,
            warehouse_id=UUID(data["warehouse_id"])
            if data.get("warehouse_id")
            else None,
            employee_id=UUID(data["employee_id"])
            if data.get("employee_id")
            else None,
            event_type="order.assembly_started",
        )

    if target_type is OrderAssembledEvent or event_type == "order.assembled":
        return OrderAssembledEvent(
            order_id=UUID(data["order_id"])
            if isinstance(data["order_id"], str)
            else data["order_id"],
            retail_point_id=UUID(data["retail_point_id"])
            if data.get("retail_point_id")
            else None,
            created_by_id=UUID(data["created_by_id"])
            if data.get("created_by_id")
            else None,
            warehouse_id=UUID(data["warehouse_id"])
            if data.get("warehouse_id")
            else None,
            employee_id=UUID(data["employee_id"])
            if data.get("employee_id")
            else None,
            event_type="order.assembled",
        )

    if target_type is OrderTakenByAgentEvent or event_type == "order.taken_by_agent":
        return OrderTakenByAgentEvent(
            order_id=UUID(data["order_id"])
            if isinstance(data["order_id"], str)
            else data["order_id"],
            retail_point_id=UUID(data["retail_point_id"])
            if data.get("retail_point_id")
            else None,
            created_by_id=UUID(data["created_by_id"])
            if data.get("created_by_id")
            else None,
            warehouse_id=UUID(data["warehouse_id"])
            if data.get("warehouse_id")
            else None,
            employee_id=UUID(data["employee_id"])
            if data.get("employee_id")
            else None,
            event_type="order.taken_by_agent",
        )

    if target_type is OrderDeliveredEvent or event_type == "order.delivered":
        return OrderDeliveredEvent(
            order_id=UUID(data["order_id"])
            if isinstance(data["order_id"], str)
            else data["order_id"],
            retail_point_id=UUID(data["retail_point_id"])
            if data.get("retail_point_id")
            else None,
            created_by_id=UUID(data["created_by_id"])
            if data.get("created_by_id")
            else None,
            warehouse_id=UUID(data["warehouse_id"])
            if data.get("warehouse_id")
            else None,
            employee_id=UUID(data["employee_id"])
            if data.get("employee_id")
            else None,
            event_type="order.delivered",
        )

    if target_type is OrderCancelledEvent or event_type == "order.cancelled":
        return OrderCancelledEvent(
            order_id=UUID(data["order_id"])
            if isinstance(data["order_id"], str)
            else data["order_id"],
            retail_point_id=UUID(data["retail_point_id"])
            if data.get("retail_point_id")
            else None,
            created_by_id=UUID(data["created_by_id"])
            if data.get("created_by_id")
            else None,
            warehouse_id=UUID(data["warehouse_id"])
            if data.get("warehouse_id")
            else None,
            event_type="order.cancelled",
        )

    if (
        target_type is OrderCreatedEvent
        or event_type == "order.created"
        or (event_type is None and "order_id" in data and "retail_point_id" in data)
    ):
        return OrderCreatedEvent(
            order_id=UUID(data["order_id"])
            if isinstance(data["order_id"], str)
            else data["order_id"],
            retail_point_id=UUID(data["retail_point_id"])
            if isinstance(data["retail_point_id"], str)
            else data["retail_point_id"],
            created_by_id=UUID(data["created_by_id"])
            if isinstance(data["created_by_id"], str)
            else data["created_by_id"],
            warehouse_id=UUID(data["warehouse_id"])
            if data.get("warehouse_id")
            else None,
            event_type=data.get("event_type", "order.created"),
        )

    return data

