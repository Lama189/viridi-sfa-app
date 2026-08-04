from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.retail_point_assignments import RetailPointAssignment
from app.infrastructure.postgres.repos.retail_point_assignments import (
    PostgresRetailPointAssignmentRepository,
)


@pytest.mark.asyncio
async def test_retail_point_assignment_repo_operations(session: AsyncSession):
    repo = PostgresRetailPointAssignmentRepository(session)
    point1 = uuid4()
    point2 = uuid4()
    emp_id = uuid4()

    a1 = RetailPointAssignment(retail_point_id=point1, employee_id=emp_id)
    a2 = RetailPointAssignment(retail_point_id=point2, employee_id=emp_id)

    await repo.add_many([a1, a2])
    await session.commit()

    found = await repo.get_by_retail_point_id(point1)
    assert found is not None
    assert found.employee_id == emp_id

    emp_assignments = await repo.list_by_employee_id(emp_id)
    assert len(emp_assignments) == 2

    assert await repo.exists_by_retail_point_id(point1) is True

    await repo.clear_employee_assignments([point1, point2])
    await session.commit()

    emp_assignments_after = await repo.list_by_employee_id(emp_id)
    assert len(emp_assignments_after) == 0
