from decimal import Decimal
from uuid import uuid4

from app.domain.entities.retail_points import RetailPoint
from app.domain.enums import ClientType


def test_retail_point_default_values():
    rp = RetailPoint(name="Store-1", address="ul. Test 1")
    assert rp.name == "Store-1"
    assert rp.address == "ul. Test 1"
    assert isinstance(rp.id, type(uuid4()))
    assert rp.legal_name is None
    assert rp.client_type == ClientType.C
    assert rp.landmark is None
    assert rp.contact_person is None
    assert rp.phone_number is None
    assert rp.inn is None
    assert rp.checking_account is None
    assert rp.bank_name is None
    assert rp.mfo is None
    assert rp.oked is None
    assert rp.latitude is None
    assert rp.longitude is None
    assert rp.photo_id is None
    assert rp.created_by_employee_id is None
    assert rp.is_active is True


def test_retail_point_custom_values():
    uid = uuid4()
    emp_id = uuid4()
    photo_id = uuid4()
    rp = RetailPoint(
        name="Big Store",
        address="ul. Main 1",
        id=uid,
        legal_name="OOO BigStore",
        client_type=ClientType.B,
        landmark="near mall",
        contact_person="John",
        phone_number="+998901234567",
        inn="123456789",
        checking_account="12345678901234567890",
        bank_name="Bank",
        mfo="12345",
        oked="12345",
        latitude=Decimal("41.311081"),
        longitude=Decimal("69.240562"),
        photo_id=photo_id,
        created_by_employee_id=emp_id,
        is_active=False,
    )
    assert rp.id == uid
    assert rp.legal_name == "OOO BigStore"
    assert rp.client_type == ClientType.B
    assert rp.landmark == "near mall"
    assert rp.contact_person == "John"
    assert rp.phone_number == "+998901234567"
    assert rp.inn == "123456789"
    assert rp.checking_account == "12345678901234567890"
    assert rp.bank_name == "Bank"
    assert rp.mfo == "12345"
    assert rp.oked == "12345"
    assert rp.latitude == Decimal("41.311081")
    assert rp.longitude == Decimal("69.240562")
    assert rp.photo_id == photo_id
    assert rp.created_by_employee_id == emp_id
    assert rp.is_active is False


def test_retail_point_client_type_b():
    rp = RetailPoint(name="B", address="A", client_type=ClientType.B)
    assert rp.client_type == ClientType.B


def test_retail_point_client_type_c():
    rp = RetailPoint(name="C", address="A", client_type=ClientType.C)
    assert rp.client_type == ClientType.C
