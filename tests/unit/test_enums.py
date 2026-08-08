from app.domain.enums import ClientType, EmployeeRole, OrderStatus, VisitStatus


def test_employee_role_values():
    assert EmployeeRole.ADMIN == "admin"
    assert EmployeeRole.AGENT == "agent"
    assert EmployeeRole.WAREHOUSE_WORKER == "warehouse_worker"


def test_client_type_values():
    assert ClientType.B == "B"
    assert ClientType.C == "C"


def test_order_status_values():
    assert OrderStatus.PENDING == "pending"
    assert OrderStatus.CONFIRMED == "confirmed"
    assert OrderStatus.ASSEMBLY_STARTED == "assembly_started"
    assert OrderStatus.ASSEMBLED == "assembled"
    assert OrderStatus.SHIPPED == "shipped"
    assert OrderStatus.DELIVERED == "delivered"
    assert OrderStatus.CANCELLED == "cancelled"


def test_visit_status_values():
    assert VisitStatus.IN_PROGRESS == "in_progress"
    assert VisitStatus.COMPLETED == "completed"
    assert VisitStatus.CANCELLED == "cancelled"


def test_employee_role_is_str_enum():
    assert isinstance(EmployeeRole.ADMIN, str)
    assert EmployeeRole("admin") == EmployeeRole.ADMIN


def test_client_type_is_str_enum():
    assert isinstance(ClientType.B, str)
    assert ClientType("B") == ClientType.B


def test_order_status_is_str_enum():
    assert isinstance(OrderStatus.PENDING, str)
    assert OrderStatus("pending") == OrderStatus.PENDING


def test_visit_status_is_str_enum():
    assert isinstance(VisitStatus.COMPLETED, str)
    assert VisitStatus("completed") == VisitStatus.COMPLETED
