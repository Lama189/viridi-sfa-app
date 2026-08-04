from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.retail_point_members import RetailPointMember
from app.infrastructure.postgres.repos.retail_point_members import (
    PostgresRetailPointMemberRepository,
)


@pytest.mark.asyncio
async def test_retail_point_member_repo_operations(session: AsyncSession):
    repo = PostgresRetailPointMemberRepository(session)
    point_id = uuid4()
    client_id = uuid4()

    member = RetailPointMember(retail_point_id=point_id, client_id=client_id)
    await repo.add(member)
    await session.commit()

    found = await repo.get_by_id(member.id)
    assert found is not None
    assert found.retail_point_id == point_id
    assert found.client_id == client_id

    by_rp = await repo.get_by_retail_point(point_id)
    assert len(by_rp) == 1

    by_rp_client = await repo.get_by_retail_point_and_client(point_id, client_id)
    assert by_rp_client is not None
    assert by_rp_client.id == member.id

    assert await repo.exists(point_id, client_id) is True

    await repo.delete(member)
    await session.commit()

    deleted = await repo.get_by_id(member.id)
    assert deleted is None
