from dataclasses import dataclass
from uuid import UUID
from decimal import Decimal

from app.domain.entities.retail_points import RetailPoint


@dataclass(slots=True)
class TerritoryCluster:
    id: UUID
    retail_points: list[RetailPoint]
    center_latitude: Decimal
    center_longitude: Decimal