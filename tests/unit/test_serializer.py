import json
from datetime import UTC, datetime
from uuid import uuid4

from app.infrastructure.rabbitmq.serializer import serialize_event


def test_serialize_event_basic():
    payload = {"key": "value", "count": 42}
    result = serialize_event(payload)
    assert isinstance(result, bytes)

    decoded = json.loads(result.decode("utf-8"))
    assert decoded == payload


def test_serialize_event_with_uuid_and_datetime():
    sample_id = uuid4()
    now = datetime.now(UTC)
    payload = {
        "id": sample_id,
        "timestamp": now,
        "nested": {"another_id": sample_id},
    }

    result = serialize_event(payload)
    decoded = json.loads(result.decode("utf-8"))

    assert decoded["id"] == str(sample_id)
    assert decoded["timestamp"] == now.isoformat()
    assert decoded["nested"]["another_id"] == str(sample_id)
