from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.application.services.retail_point_assignments import RetailPointAssignmentService
from app.core.extensions import (
    RetailPointNotFoundError,
    RetailPointInactiveError,
    RetailPointAssignmentNotFoundError,
    RetailPointAssignmentAlreadyExistsError,
    UserNotFoundError,
    UserNotActiveError,
)


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.employees = AsyncMock()
    uow.retail_point_assignments = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return RetailPointAssignmentService(mock_uow)


# --- create ---

@pytest.mark.asyncio
async def test_create_success(service, mock_uow):
    retail_point_id = uuid4()

    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.exists_by_retail_point_id.return_value = False
    mock_uow.retail_point_assignments.add.return_value = None

    result = await service.create(retail_point_id)

    assert result.retail_point_id == retail_point_id
    assert result.employee_id is None
    mock_uow.retail_point_assignments.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.create(uuid4())


@pytest.mark.asyncio
async def test_create_retail_point_inactive(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=False)

    with pytest.raises(RetailPointInactiveError):
        await service.create(uuid4())


@pytest.mark.asyncio
async def test_create_already_exists(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.exists_by_retail_point_id.return_value = True

    with pytest.raises(RetailPointAssignmentAlreadyExistsError):
        await service.create(uuid4())


# --- delete ---

@pytest.mark.asyncio
async def test_delete_success(service, mock_uow):
    retail_point_id = uuid4()
    assignment = MagicMock()

    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment
    mock_uow.retail_point_assignments.delete.return_value = None

    await service.delete(retail_point_id)

    mock_uow.retail_point_assignments.delete.assert_awaited_once_with(assignment)


@pytest.mark.asyncio
async def test_delete_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.delete(uuid4())


@pytest.mark.asyncio
async def test_delete_assignment_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = None

    with pytest.raises(RetailPointAssignmentNotFoundError):
        await service.delete(uuid4())


# --- assign_employee ---

@pytest.mark.asyncio
async def test_assign_employee_success(service, mock_uow):
    retail_point_id = uuid4()
    employee_id = uuid4()
    assignment = MagicMock()

    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.employees.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment
    mock_uow.retail_point_assignments.update.return_value = None

    result = await service.assign_employee(retail_point_id, employee_id)

    assert result == assignment
    mock_uow.retail_point_assignments.update.assert_awaited_once_with(assignment)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_assign_employee_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.assign_employee(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_assign_employee_retail_point_inactive(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=False)

    with pytest.raises(RetailPointInactiveError):
        await service.assign_employee(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_assign_employee_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.employees.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await service.assign_employee(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_assign_employee_inactive(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.employees.get_by_id.return_value = MagicMock(is_active=False)

    with pytest.raises(UserNotActiveError):
        await service.assign_employee(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_assign_employee_assignment_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.employees.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = None

    with pytest.raises(RetailPointAssignmentNotFoundError):
        await service.assign_employee(uuid4(), uuid4())


# --- unassign_employee ---

@pytest.mark.asyncio
async def test_unassign_employee_success(service, mock_uow):
    retail_point_id = uuid4()
    assignment = MagicMock()

    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = assignment
    mock_uow.retail_point_assignments.update.return_value = None

    result = await service.unassign_employee(retail_point_id)

    assert result == assignment
    assignment.remove_employee.assert_called_once()
    mock_uow.retail_point_assignments.update.assert_awaited_once_with(assignment)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_unassign_employee_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.unassign_employee(uuid4())


@pytest.mark.asyncio
async def test_unassign_employee_assignment_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = MagicMock(is_active=True)
    mock_uow.retail_point_assignments.get_by_retail_point_id.return_value = None

    with pytest.raises(RetailPointAssignmentNotFoundError):
        await service.unassign_employee(uuid4())
