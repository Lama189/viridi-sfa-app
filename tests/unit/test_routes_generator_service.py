from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.routes_generator import RouteGenerationService
from app.core.exceptions import (
    NoActiveAgentsFoundError,
    NoActiveRetailPointsError,
    TerritoryClustersNotBuiltError,
)
from app.domain.entities.employees import Employee
from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.territories import TerritoryCluster
from app.domain.enums import EmployeeRole


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.employees = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_clustering_service():
    return AsyncMock()


@pytest.fixture
def mock_assignments_service():
    return AsyncMock()


@pytest.fixture
def mock_visit_plans_service():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_clustering_service, mock_assignments_service, mock_visit_plans_service):
    return RouteGenerationService(
        uow=mock_uow,
        clustering_service=mock_clustering_service,
        assignments_service=mock_assignments_service,
        visit_plans_service=mock_visit_plans_service,
    )


@pytest.mark.asyncio
async def test_generate_no_active_agents(service, mock_uow):
    mock_uow.employees.list_by.return_value = []

    with pytest.raises(NoActiveAgentsFoundError):
        await service.generate()


@pytest.mark.asyncio
async def test_generate_no_retail_points(service, mock_uow):
    mock_uow.employees.list_by.return_value = [Employee(phone="1", password_hash="1", full_name="A")]
    mock_uow.retail_points.list_all.return_value = []

    with pytest.raises(NoActiveRetailPointsError):
        await service.generate()


@pytest.mark.asyncio
async def test_generate_clusters_not_built(service, mock_uow, mock_clustering_service):
    mock_uow.employees.list_by.return_value = [Employee(phone="1", password_hash="1", full_name="A")]
    mock_uow.retail_points.list_all.return_value = [RetailPoint(name="P1", address="A1")]
    mock_clustering_service.build_clusters.return_value = []

    with pytest.raises(TerritoryClustersNotBuiltError):
        await service.generate()


@pytest.mark.asyncio
async def test_generate_success(
    service,
    mock_uow,
    mock_clustering_service,
    mock_assignments_service,
    mock_visit_plans_service,
):
    agent1 = Employee(phone="1", password_hash="1", full_name="A1", role=EmployeeRole.AGENT)
    point1 = RetailPoint(name="P1", address="A1")
    cluster1 = TerritoryCluster(
        id=uuid4(),
        retail_points=[point1],
        center_latitude=point1.latitude or 0,
        center_longitude=point1.longitude or 0,
    )

    mock_uow.employees.list_by.return_value = [agent1]
    mock_uow.retail_points.list_all.return_value = [point1]
    mock_clustering_service.build_clusters.return_value = [cluster1]

    await service.generate()

    mock_assignments_service.clear_employee_assignments.assert_awaited_once_with([point1.id])
    mock_assignments_service.assign_employee.assert_awaited_once_with(
        retail_point_id=point1.id,
        employee_id=agent1.id,
    )
    assert mock_visit_plans_service.generate_for_employee.await_count == 7
    mock_uow.commit.assert_awaited_once()
