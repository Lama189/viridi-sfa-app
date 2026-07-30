from abc import ABC, abstractmethod

from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.territories import TerritoryCluster


class ITerritoryClusteringService(ABC):

    @abstractmethod
    async def build_clusters(
        self,
        points: list[RetailPoint],
        agents_count: int,
    ) -> list[TerritoryCluster]:
        raise NotImplementedError