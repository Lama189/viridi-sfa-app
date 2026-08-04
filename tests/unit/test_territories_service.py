from decimal import Decimal

import pytest

from app.application.services.territories import TerritoryClusteringService
from app.core.exceptions import InvalidEmployeesCountError
from app.domain.entities.retail_points import RetailPoint


@pytest.fixture
def service():
    return TerritoryClusteringService()


@pytest.mark.asyncio
async def test_build_clusters_invalid_agents_count(service):
    with pytest.raises(InvalidEmployeesCountError):
        await service.build_clusters([], agents_count=0)


@pytest.mark.asyncio
async def test_build_clusters_empty_points(service):
    clusters = await service.build_clusters([], agents_count=3)
    assert clusters == []


@pytest.mark.asyncio
async def test_build_clusters_points_without_coordinates(service):
    p1 = RetailPoint(name="P1", address="A1", latitude=None, longitude=None)
    clusters = await service.build_clusters([p1], agents_count=2)
    assert clusters == []


@pytest.mark.asyncio
async def test_build_clusters_single_cluster(service):
    p1 = RetailPoint(name="P1", address="A1", latitude=Decimal("41.31"), longitude=Decimal("69.24"))
    clusters = await service.build_clusters([p1], agents_count=1)

    assert len(clusters) == 1
    assert len(clusters[0].retail_points) == 1
    assert clusters[0].center_latitude == Decimal("41.31")
    assert clusters[0].center_longitude == Decimal("69.24")


@pytest.mark.asyncio
async def test_build_clusters_multiple_agents_and_points(service):
    points = [
        RetailPoint(
            name=f"P{i}",
            address=f"A{i}",
            latitude=Decimal(f"41.3{i}"),
            longitude=Decimal(f"69.2{i}"),
        )
        for i in range(10)
    ]

    clusters = await service.build_clusters(points, agents_count=3)

    assert len(clusters) == 3
    total_clustered = sum(len(c.retail_points) for c in clusters)
    assert total_clustered == 10
