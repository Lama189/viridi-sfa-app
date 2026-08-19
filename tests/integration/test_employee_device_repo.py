from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.employee_devices import EmployeeDevice
from app.infrastructure.postgres.repos.employee_devices import (
    PostgresEmployeeDeviceRepository,
)


@pytest.mark.asyncio
async def test_employee_device_repo_operations(session: AsyncSession):
    repo = PostgresEmployeeDeviceRepository(session)
    employee_id = uuid4()

    device = EmployeeDevice(
        employee_id=employee_id,
        fcm_token="token_abc_123",
        device_type="android",
    )
    await repo.add_or_update(device)
    await session.commit()

    # list_by_employee
    devices = await repo.list_by_employee(employee_id)
    assert len(devices) == 1
    assert devices[0].fcm_token == "token_abc_123"
    assert devices[0].device_type == "android"

    # Upsert with same token, different device type
    device_update = EmployeeDevice(
        employee_id=employee_id,
        fcm_token="token_abc_123",
        device_type="ios",
    )
    await repo.add_or_update(device_update)
    await session.commit()

    devices_after_update = await repo.list_by_employee(employee_id)
    assert len(devices_after_update) == 1
    assert devices_after_update[0].device_type == "ios"

    # delete_by_token
    await repo.delete_by_token("token_abc_123")
    await session.commit()

    devices_after_delete = await repo.list_by_employee(employee_id)
    assert len(devices_after_delete) == 0

    # Test delete_by_tokens
    d1 = EmployeeDevice(employee_id=employee_id, fcm_token="tok_batch_1")
    d2 = EmployeeDevice(employee_id=employee_id, fcm_token="tok_batch_2")
    d3 = EmployeeDevice(employee_id=employee_id, fcm_token="tok_batch_3")
    await repo.add_or_update(d1)
    await repo.add_or_update(d2)
    await repo.add_or_update(d3)
    await session.commit()

    assert len(await repo.list_by_employee(employee_id)) == 3

    await repo.delete_by_tokens(["tok_batch_1", "tok_batch_3"])
    await session.commit()

    remaining = await repo.list_by_employee(employee_id)
    assert len(remaining) == 1
    assert remaining[0].fcm_token == "tok_batch_2"
