from uuid import uuid4

from app.domain.entities.retail_point_members import RetailPointMember


def test_retail_point_member_default_values():
    rp_id = uuid4()
    client_id = uuid4()
    member = RetailPointMember(retail_point_id=rp_id, client_id=client_id)
    assert member.retail_point_id == rp_id
    assert member.client_id == client_id
    assert isinstance(member.id, type(uuid4()))
    assert member.created_at is not None


def test_retail_point_member_different_instances():
    m1 = RetailPointMember(retail_point_id=uuid4(), client_id=uuid4())
    m2 = RetailPointMember(retail_point_id=uuid4(), client_id=uuid4())
    assert m1.id != m2.id
