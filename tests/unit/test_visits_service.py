from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.services.visits import VisitService
from app.core.exceptions import (
    EmployeeHasActiveVisitError,
    MediaNotFoundError,
    RetailPointInactiveError,
    RetailPointNotFoundError,
    VisitNotActiveError,
    VisitNotFoundError,
)
from app.domain.entities.visits import Visit
from app.domain.enums import VisitStatus


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.visits = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.media_objects = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_visit_media_service():
    return AsyncMock()


@pytest.fixture
def mock_visit_debts_service():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_visit_media_service, mock_visit_debts_service):
    return VisitService(mock_uow, mock_visit_media_service, mock_visit_debts_service)


# --- start_visit ---


@pytest.mark.asyncio
async def test_start_visit_success(service, mock_uow):
    employee_id = uuid4()
    retail_point_id = uuid4()

    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.visits.list_by_employee.return_value = []
    mock_uow.visits.add.return_value = None

    result = await service.start_visit(employee_id, retail_point_id)

    assert result.employee_id == employee_id
    assert result.retail_point_id == retail_point_id
    assert result.status == VisitStatus.IN_PROGRESS
    mock_uow.visits.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_visit_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.start_visit(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_start_visit_retail_point_inactive(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=False)

    with pytest.raises(RetailPointInactiveError):
        await service.start_visit(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_start_visit_already_active(service, mock_uow):
    employee_id = uuid4()
    retail_point_id = uuid4()

    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.visits.list_by_employee.return_value = [
        Visit(
            employee_id=employee_id,
            retail_point_id=retail_point_id,
        )
    ]

    with pytest.raises(EmployeeHasActiveVisitError):
        await service.start_visit(employee_id, retail_point_id)


# --- finish_visit ---


@pytest.mark.asyncio
async def test_finish_visit_success(service, mock_uow):
    visit_id = uuid4()
    visit = Visit(
        employee_id=uuid4(),
        retail_point_id=uuid4(),
        started_at=datetime.now(UTC),
    )
    visit.id = visit_id

    mock_uow.visits.get_by_id.return_value = visit
    mock_uow.visits.update.return_value = None

    result = await service.finish_visit(visit_id)

    assert result.status == VisitStatus.COMPLETED
    assert result.finished_at is not None
    mock_uow.visits.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_finish_visit_not_found(service, mock_uow):
    mock_uow.visits.get_by_id.return_value = None

    with pytest.raises(VisitNotFoundError):
        await service.finish_visit(uuid4())


# --- cancel_visit ---


@pytest.mark.asyncio
async def test_cancel_visit_success(service, mock_uow):
    visit_id = uuid4()
    visit = Visit(
        employee_id=uuid4(),
        retail_point_id=uuid4(),
        started_at=datetime.now(UTC),
    )
    visit.id = visit_id

    mock_uow.visits.get_by_id.return_value = visit
    mock_uow.visits.update.return_value = None

    result = await service.cancel_visit(visit_id)

    assert result.status == VisitStatus.CANCELLED
    assert result.finished_at is not None
    mock_uow.visits.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_visit_not_found(service, mock_uow):
    mock_uow.visits.get_by_id.return_value = None

    with pytest.raises(VisitNotFoundError):
        await service.cancel_visit(uuid4())


# --- get_visit ---


@pytest.mark.asyncio
async def test_get_visit_found(service, mock_uow):
    visit_id = uuid4()
    visit = Visit(
        employee_id=uuid4(),
        retail_point_id=uuid4(),
    )
    visit.id = visit_id

    mock_uow.visits.get_by_id.return_value = visit

    result = await service.get_visit(visit_id)

    assert result.id == visit_id


@pytest.mark.asyncio
async def test_get_visit_not_found(service, mock_uow):
    mock_uow.visits.get_by_id.return_value = None

    with pytest.raises(VisitNotFoundError):
        await service.get_visit(uuid4())


# --- list ---


@pytest.mark.asyncio
async def test_list_visits(service, mock_uow):
    mock_uow.visits.list.return_value = []

    result = await service.list()

    assert result == []
    mock_uow.visits.list.assert_awaited_once_with(None, None, None)


@pytest.mark.asyncio
async def test_list_visits_with_filters(service, mock_uow):
    employee_id = uuid4()
    retail_point_id = uuid4()

    mock_uow.visits.list.return_value = []

    result = await service.list(
        employee_id=employee_id,
        retail_point_id=retail_point_id,
        status=VisitStatus.IN_PROGRESS,
    )

    assert result == []
    mock_uow.visits.list.assert_awaited_once_with(
        employee_id,
        retail_point_id,
        VisitStatus.IN_PROGRESS,
    )


@pytest.mark.asyncio
async def test_list_visits_validates_retail_point(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=False)

    with pytest.raises(RetailPointInactiveError):
        await service.list(retail_point_id=uuid4())


# --- attach_media ---


@pytest.mark.asyncio
async def test_attach_media_success(service, mock_uow, mock_visit_media_service):
    visit_id = uuid4()
    media_id = uuid4()

    mock_uow.media_objects.get_by_id.return_value = MagicMock()
    mock_uow.visits.get_by_id.return_value = Visit(
        employee_id=uuid4(),
        retail_point_id=uuid4(),
        started_at=datetime.now(UTC),
    )

    media = MagicMock()
    mock_visit_media_service.attach.return_value = media

    result = await service.attach_media(visit_id, media_id)

    assert result == media
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_attach_media_media_not_found(service, mock_uow):
    mock_uow.media_objects.get_by_id.return_value = None

    with pytest.raises(MediaNotFoundError):
        await service.attach_media(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_attach_media_visit_not_found(service, mock_uow):
    mock_uow.media_objects.get_by_id.return_value = MagicMock()
    mock_uow.visits.get_by_id.return_value = None

    with pytest.raises(VisitNotFoundError):
        await service.attach_media(uuid4(), uuid4())


# --- detach_media ---


@pytest.mark.asyncio
async def test_detach_media_success(service, mock_uow, mock_visit_media_service):
    visit_id = uuid4()
    media_id = uuid4()

    mock_uow.media_objects.get_by_id.return_value = MagicMock()
    mock_uow.visits.get_by_id.return_value = Visit(
        employee_id=uuid4(),
        retail_point_id=uuid4(),
        started_at=datetime.now(UTC),
    )
    mock_visit_media_service.detach.return_value = None

    await service.detach_media(visit_id, media_id)

    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_detach_media_not_found(service, mock_uow):
    mock_uow.media_objects.get_by_id.return_value = None

    with pytest.raises(MediaNotFoundError):
        await service.detach_media(uuid4(), uuid4())


# --- add_debt ---


@pytest.mark.asyncio
async def test_add_debt_success(service, mock_uow, mock_visit_debts_service):
    visit_id = uuid4()

    mock_uow.visits.get_by_id.return_value = Visit(
        employee_id=uuid4(),
        retail_point_id=uuid4(),
        started_at=datetime.now(UTC),
    )

    debt = MagicMock()
    mock_visit_debts_service.add.return_value = debt

    result = await service.add_debt(visit_id, Decimal("50000.00"), "Test")

    assert result == debt
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_debt_visit_not_found(service, mock_uow):
    mock_uow.visits.get_by_id.return_value = None

    with pytest.raises(VisitNotFoundError):
        await service.add_debt(uuid4(), Decimal("50000.00"), "Test")


@pytest.mark.asyncio
async def test_add_debt_visit_not_active(service, mock_uow):
    mock_uow.visits.get_by_id.return_value = Visit(
        employee_id=uuid4(),
        retail_point_id=uuid4(),
    )

    with pytest.raises(VisitNotActiveError):
        await service.add_debt(uuid4(), Decimal("50000.00"), "Test")


# --- update_debt ---


@pytest.mark.asyncio
async def test_update_debt_success(service, mock_uow, mock_visit_debts_service):
    debt_id = uuid4()
    mock_visit_debts_service.get_by_id.return_value = MagicMock()
    mock_visit_debts_service.update.return_value = MagicMock()

    await service.update_debt(debt_id, Decimal("75000.00"), "Updated")

    mock_uow.commit.assert_awaited_once()


# --- delete_debt ---


@pytest.mark.asyncio
async def test_delete_debt_success(service, mock_uow, mock_visit_debts_service):
    debt_id = uuid4()
    mock_visit_debts_service.get_by_id.return_value = MagicMock()
    mock_visit_debts_service.delete.return_value = None

    await service.delete_debt(debt_id)

    mock_uow.commit.assert_awaited_once()
