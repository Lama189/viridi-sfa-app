from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.notifications import Notification
from app.infrastructure.postgres.repos.notifications import (
    PostgresNotificationRepository,
)


@pytest.mark.asyncio
async def test_notification_repo_crud_operations(session: AsyncSession):
    repo = PostgresNotificationRepository(session)
    employee_id = uuid4()

    notification = Notification(
        employee_id=employee_id,
        title="Новый заказ",
        body="Заказ готов к доставке",
        notification_type="order_delivery_proposal",
        payload={"order_id": str(uuid4())},
    )
    await repo.add(notification)
    await session.commit()

    # get_by_id
    found = await repo.get_by_id(notification.id)
    assert found is not None
    assert found.employee_id == employee_id
    assert found.title == "Новый заказ"
    assert found.body == "Заказ готов к доставке"
    assert found.notification_type == "order_delivery_proposal"
    assert found.is_read is False

    # list_by_employee
    notifications = await repo.list_by_employee(employee_id)
    assert len(notifications) == 1
    assert notifications[0].id == notification.id

    # count_unread_by_employee
    unread_count = await repo.count_unread_by_employee(employee_id)
    assert unread_count == 1

    # mark_all_as_read
    await repo.mark_all_as_read(employee_id)
    await session.commit()

    found_after_read = await repo.get_by_id(notification.id)
    assert found_after_read is not None
    assert found_after_read.is_read is True
    assert found_after_read.read_at is not None

    unread_count_after = await repo.count_unread_by_employee(employee_id)
    assert unread_count_after == 0

    # delete
    await repo.delete(notification.id)
    await session.commit()

    deleted = await repo.get_by_id(notification.id)
    assert deleted is None
