from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.employees import Employee
from app.infrastructure.postgres.repos.employees import PostgresEmployeeRepository


@pytest.mark.asyncio
async def test_add_and_get_by_id(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    e = Employee(
        phone="+998901234567", password_hash="hash123", full_name="Test Employee"
    )
    await employee_repo.add(e)
    await session.commit()

    found = await employee_repo.get_by_id(e.id)
    assert found is not None
    assert found.phone == "+998901234567"
    assert found.full_name == "Test Employee"
    assert found.password_hash == "hash123"
    assert found.is_active is True


@pytest.mark.asyncio
async def test_get_by_id_not_found(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    found = await employee_repo.get_by_id(uuid4())
    assert found is None


@pytest.mark.asyncio
async def test_get_by_found(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    e = Employee(
        phone="+998909999999", password_hash="hash", full_name="Lookup Employee"
    )
    await employee_repo.add(e)
    await session.commit()

    found = await employee_repo.get_by(phone="+998909999999")
    assert found is not None
    assert found.full_name == "Lookup Employee"


@pytest.mark.asyncio
async def test_get_by_not_found(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    found = await employee_repo.get_by(phone="+998900000000")
    assert found is None


@pytest.mark.asyncio
async def test_exists_by_true(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    e = Employee(phone="+998901111111", password_hash="hash", full_name="Exists")
    await employee_repo.add(e)
    await session.commit()

    assert await employee_repo.exists_by(phone="+998901111111") is True


@pytest.mark.asyncio
async def test_exists_by_false(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    assert await employee_repo.exists_by(phone="+998900000000") is False


@pytest.mark.asyncio
async def test_list_by(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    await employee_repo.add(
        Employee(phone="+998903000001", password_hash="h", full_name="Agent1")
    )
    await employee_repo.add(
        Employee(phone="+998903000002", password_hash="h", full_name="Agent2")
    )
    await employee_repo.add(
        Employee(
            phone="+998903000003", password_hash="h", full_name="Admin1", role="admin"
        )
    )
    await session.commit()

    agents = await employee_repo.list_by(role="agent")
    assert len(agents) == 2

    admins = await employee_repo.list_by(role="admin")
    assert len(admins) == 1


@pytest.mark.asyncio
async def test_list_by_empty(
    session: AsyncSession, employee_repo: PostgresEmployeeRepository
):
    result = await employee_repo.list_by(role="admin")
    assert result == []


@pytest.mark.asyncio
async def test_update(session: AsyncSession, employee_repo: PostgresEmployeeRepository):
    e = Employee(phone="+998905000000", password_hash="old", full_name="Old Name")
    await employee_repo.add(e)
    await session.commit()

    e.full_name = "New Name"
    e.password_hash = "new_hash"
    e.role = "admin"
    await employee_repo.update(e)
    await session.commit()

    found = await employee_repo.get_by_id(e.id)
    assert found.full_name == "New Name"
    assert found.password_hash == "new_hash"
    assert str(found.role) == "admin"


@pytest.mark.asyncio
async def test_delete(session: AsyncSession, employee_repo: PostgresEmployeeRepository):
    e = Employee(phone="+998906000000", password_hash="hash", full_name="ToDelete")
    await employee_repo.add(e)
    await session.commit()

    await employee_repo.delete(e)
    await session.commit()

    found = await employee_repo.get_by_id(e.id)
    assert found is None
