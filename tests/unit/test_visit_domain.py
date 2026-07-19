from decimal import Decimal
from uuid import uuid4

from app.domain.entities.visits import Visit, VisitPhoto, VisitWithPhotos


def test_visit_default_values():
    agent_id = uuid4()
    rp_id = uuid4()
    v = Visit(agent_id=agent_id, retail_point_id=rp_id)
    assert v.agent_id == agent_id
    assert v.retail_point_id == rp_id
    assert isinstance(v.id, type(uuid4()))
    assert v.check_in_time is not None
    assert v.check_out_time is None
    assert v.actual_latitude is None
    assert v.actual_longitude is None
    assert v.status == "completed"
    assert v.comment is None


def test_visit_custom_values():
    agent_id = uuid4()
    rp_id = uuid4()
    visit_id = uuid4()
    v = Visit(
        agent_id=agent_id,
        retail_point_id=rp_id,
        id=visit_id,
        status="skipped",
        comment="Was closed",
        actual_latitude=Decimal("41.311081"),
        actual_longitude=Decimal("69.240562"),
    )
    assert v.id == visit_id
    assert v.status == "skipped"
    assert v.comment == "Was closed"
    assert v.actual_latitude == Decimal("41.311081")
    assert v.actual_longitude == Decimal("69.240562")


def test_visit_photo_default_values():
    visit_id = uuid4()
    photo = VisitPhoto(visit_id=visit_id, photo_url="/photos/1.jpg")
    assert photo.visit_id == visit_id
    assert photo.photo_url == "/photos/1.jpg"
    assert isinstance(photo.id, type(uuid4()))
    assert photo.created_at is not None


def test_visit_with_photos_empty():
    visit = Visit(agent_id=uuid4(), retail_point_id=uuid4())
    vwp = VisitWithPhotos(visit=visit)
    assert vwp.visit is visit
    assert vwp.photos == []


def test_visit_with_photos_with_items():
    visit = Visit(agent_id=uuid4(), retail_point_id=uuid4())
    photo1 = VisitPhoto(visit_id=visit.id, photo_url="/a.jpg")
    photo2 = VisitPhoto(visit_id=visit.id, photo_url="/b.jpg")
    vwp = VisitWithPhotos(visit=visit, photos=[photo1, photo2])
    assert len(vwp.photos) == 2
