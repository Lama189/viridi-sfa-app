from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.visits import Visit
from app.domain.enums import VisitStatus
from app.infrastructure.postgres.repos.visits import PostgresVisitRepository


@pytest.mark.asyncio
async def test_visit_repo_operations(session: AsyncSession):
    repo = PostgresVisitRepository(session)
    emp_id = uuid4()
    point_id = uuid4()

    visit = Visit(employee_id=emp_id, retail_point_id=point_id)
    await repo.add(visit)
    await session.commit()

    found = await repo.get_by_id(visit.id)
    assert found is not None
    assert found.employee_id == emp_id
    assert found.retail_point_id == point_id

    visits_emp = await repo.list_by_employee(emp_id, active=False)
    assert len(visits_emp) == 1

    visits_point = await repo.list_by_retail_point(point_id)
    assert len(visits_point) == 1

    assert await repo.exists_by(employee_id=emp_id) is True

    visit.status = VisitStatus.COMPLETED
    await repo.update(visit)
    await session.commit()

    updated = await repo.get_by_id(visit.id)
    assert updated.status == VisitStatus.COMPLETED

    await repo.delete(visit)
    await session.commit()

    deleted = await repo.get_by_id(visit.id)
    assert deleted is None
