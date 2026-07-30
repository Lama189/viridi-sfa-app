from uuid import uuid4

from app.domain.entities.retail_point_assignments import RetailPointAssignment


def test_retail_point_assignment_operations():
    point_id = uuid4()
    emp_id = uuid4()

    assignment = RetailPointAssignment(retail_point_id=point_id, employee_id=None)

    assert assignment.retail_point_id == point_id
    assert assignment.employee_id is None
    assert assignment.is_assigned is False

    assignment.assign_employee(emp_id)
    assert assignment.employee_id == emp_id
    assert assignment.is_assigned is True

    assignment.remove_employee()
    assert assignment.employee_id is None
    assert assignment.is_assigned is False
