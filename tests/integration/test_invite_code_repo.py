from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.invite_codes import ClientInviteCode
from app.infrastructure.postgres.repos.invite_codes import PostgresInviteCodeRepository


@pytest.mark.asyncio
async def test_invite_code_repo_operations(session: AsyncSession):
    repo = PostgresInviteCodeRepository(session)
    point_id = uuid4()
    emp_id = uuid4()

    code = ClientInviteCode(
        retail_point_id=point_id,
        encrypted_code="enc-123",
        code_hash="hash-123",
        created_by_employee_id=emp_id,
    )

    await repo.add(code)
    await session.commit()

    found = await repo.get_by_id(code.id)
    assert found is not None
    assert found.code_hash == "hash-123"

    by_point = await repo.get_by_retail_point(point_id)
    assert by_point is not None
    assert by_point.id == code.id

    by_hash = await repo.get_by_code_hash("hash-123")
    assert by_hash is not None
    assert by_hash.id == code.id

    assert await repo.exists(point_id, "hash-123") is True
