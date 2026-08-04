import json
from datetime import datetime
from typing import Any
from uuid import UUID


class JSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, datetime):
            return obj.isoformat()

        return super().default(obj)


def serialize_event(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, cls=JSONEncoder).encode("utf-8")
