from decimal import Decimal
from uuid import uuid4

import numpy as np
from k_means_constrained import KMeansConstrained

from app.application.interfaces.services.territories import ITerritoryClusteringService
from app.core.exceptions import InvalidEmployeesCountError
from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.territories import TerritoryCluster


class TerritoryClusteringService(ITerritoryClusteringService):
    def __init__(self) -> None: ...

    async def build_clusters(
        self,
        points: list[RetailPoint],
        agents_count: int,
    ) -> list[TerritoryCluster]:
        if agents_count <= 0:
            raise InvalidEmployeesCountError()

        if not points:
            return []

        valid_points = [
            point
            for point in points
            if point.latitude is not None and point.longitude is not None
        ]

        points_without_coords = [
            point
            for point in points
            if point.latitude is None or point.longitude is None
        ]

        if not valid_points:
            return []

        target_clusters_count = min(agents_count, len(valid_points))
        if target_clusters_count == 1:
            clusters = [self._create_cluster(valid_points)]
        elif len(valid_points) == target_clusters_count:
            clusters = [self._create_cluster([point]) for point in valid_points]
        else:
            coordinates = np.array(
                [[float(p.latitude), float(p.longitude)] for p in valid_points],
                dtype=np.float64,
            )

            average_size = len(valid_points) / target_clusters_count
            min_size = max(1, int(average_size * 0.7))
            max_size = max(min_size, int(np.ceil(average_size * 1.3)))

            if min_size * target_clusters_count > len(valid_points):
                min_size = max(1, len(valid_points) // target_clusters_count)
            if max_size * target_clusters_count < len(valid_points):
                max_size = int(np.ceil(len(valid_points) / target_clusters_count))

            clf = KMeansConstrained(
                n_clusters=target_clusters_count,
                size_min=min_size,
                size_max=max_size,
                random_state=42,
            )
            labels = clf.fit_predict(coordinates)

            grouped_points: dict[int, list[RetailPoint]] = {
                i: [] for i in range(target_clusters_count)
            }
            for point, label in zip(valid_points, labels):
                grouped_points[label].append(point)

            clusters = [
                self._create_cluster(cluster_points)
                for cluster_points in grouped_points.values()
                if cluster_points
            ]

        if points_without_coords and clusters:
            for idx, pt in enumerate(points_without_coords):
                clusters[idx % len(clusters)].retail_points.append(pt)

        return clusters

    def _create_cluster(self, points: list[RetailPoint]) -> TerritoryCluster:
        valid = [
            p for p in points if p.latitude is not None and p.longitude is not None
        ]
        if valid:
            avg_lat = sum(Decimal(str(p.latitude)) for p in valid) / len(valid)
            avg_lon = sum(Decimal(str(p.longitude)) for p in valid) / len(valid)
        else:
            avg_lat = Decimal(0)
            avg_lon = Decimal(0)

        return TerritoryCluster(
            id=uuid4(),
            retail_points=points,
            center_latitude=avg_lat,
            center_longitude=avg_lon,
        )
