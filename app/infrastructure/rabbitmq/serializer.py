import json
from datetime import datetime
from uuid import UUID
from typing import Any


class JSONEncoder(json.JSONEncoder):

    def default(self, obj: Any) -> Any:
        if isinstance(obj, UUID):
            return str(obj)

        if isinstance(obj, datetime):
            return obj.isoformat()

        return super().default(obj)


def serialize_event(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, cls=JSONEncoder).encode("utf-8")