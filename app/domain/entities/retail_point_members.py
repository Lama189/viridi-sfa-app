from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass(slots=True)
class RetailPointMember:
    retail_point_id: UUID
    client_id: UUID

    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.now)
