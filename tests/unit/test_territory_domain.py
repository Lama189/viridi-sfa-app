from decimal import Decimal
from uuid import uuid4

from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.territories import TerritoryCluster


def test_territory_cluster_creation():
    cid = uuid4()
    p1 = RetailPoint(
        name="P1",
        address="A1",
        latitude=Decimal("41.311081"),
        longitude=Decimal("69.240562"),
    )
    p2 = RetailPoint(
        name="P2",
        address="A2",
        latitude=Decimal("41.321081"),
        longitude=Decimal("69.250562"),
    )

    cluster = TerritoryCluster(
        id=cid,
        retail_points=[p1, p2],
        center_latitude=Decimal("41.316081"),
        center_longitude=Decimal("69.245562"),
    )

    assert cluster.id == cid
    assert len(cluster.retail_points) == 2
    assert cluster.center_latitude == Decimal("41.316081")
    assert cluster.center_longitude == Decimal("69.245562")
