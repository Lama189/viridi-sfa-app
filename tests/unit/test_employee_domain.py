from uuid import uuid4

from app.domain.entities.employees import Employee
from app.domain.enums import EmployeeRole


def test_employee_default_values():
    e = Employee(phone="+998901234567", password_hash="hash", full_name="Test Employee")
    assert e.phone == "+998901234567"
    assert e.password_hash == "hash"
    assert e.full_name == "Test Employee"
    assert isinstance(e.id, type(uuid4()))
    assert e.role == EmployeeRole.AGENT
    assert e.is_active is True


def test_employee_custom_values():
    uid = uuid4()
    e = Employee(
        phone="+998909999999",
        password_hash="hashed",
        full_name="Admin",
        id=uid,
        role=EmployeeRole.ADMIN,
        is_active=False,
    )
    assert e.id == uid
    assert e.role == EmployeeRole.ADMIN
    assert e.is_active is False


def test_employee_role_admin():
    e = Employee(
        phone="+998901234567", password_hash="h", full_name="A", role=EmployeeRole.ADMIN
    )
    assert e.role == EmployeeRole.ADMIN


def test_employee_role_agent():
    e = Employee(phone="+998901234567", password_hash="h", full_name="A")
    assert e.role == EmployeeRole.AGENT


def test_employee_is_active_toggle():
    e = Employee(phone="+998901234567", password_hash="h", full_name="X")
    e.is_active = False
    assert e.is_active is False
    e.is_active = True
    assert e.is_active is True
