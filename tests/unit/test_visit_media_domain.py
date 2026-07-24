from uuid import uuid4

from app.domain.entities.visit_media import VisitMedia


def test_visit_media_default_values():
    visit_id = uuid4()
    media_id = uuid4()
    vm = VisitMedia(visit_id=visit_id, media_id=media_id)
    assert vm.visit_id == visit_id
    assert vm.media_id == media_id
    assert isinstance(vm.id, type(uuid4()))
    assert vm.created_at is not None


def test_visit_media_different_instances():
    vm1 = VisitMedia(visit_id=uuid4(), media_id=uuid4())
    vm2 = VisitMedia(visit_id=uuid4(), media_id=uuid4())
    assert vm1.id != vm2.id
