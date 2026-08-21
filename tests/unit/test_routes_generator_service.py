from datetime import date
from unittest.mock import AsyncMock, patch
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
from app.domain.enums import EmployeeRole, RouteGenerationStart


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.employees = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.visit_plans = AsyncMock()
    uow.orders = AsyncMock()
    uow.orders.list = AsyncMock(return_value=[])
    uow.retail_point_assignments = AsyncMock()
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
def service(
    mock_uow,
    mock_clustering_service,
    mock_assignments_service,
    mock_visit_plans_service,
):
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
    mock_uow.employees.list_by.return_value = [
        Employee(phone="1", password_hash="1", full_name="A")
    ]
    mock_uow.retail_points.list_all.return_value = []

    with pytest.raises(NoActiveRetailPointsError):
        await service.generate()


@pytest.mark.asyncio
async def test_generate_clusters_not_built(service, mock_uow, mock_clustering_service):
    mock_uow.employees.list_by.return_value = [
        Employee(phone="1", password_hash="1", full_name="A")
    ]
    mock_uow.retail_points.list_all.return_value = [
        RetailPoint(name="P1", address="A1")
    ]
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
    agent1 = Employee(
        phone="1", password_hash="1", full_name="A1", role=EmployeeRole.AGENT
    )
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

    mock_assignments_service.clear_employee_assignments.assert_awaited_once_with(
        [point1.id]
    )
    mock_assignments_service.assign_employee.assert_awaited_once_with(
        retail_point_id=point1.id,
        employee_id=agent1.id,
    )
    assert mock_visit_plans_service.generate_for_employee.await_count == 7
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_start_today(
    service,
    mock_uow,
    mock_clustering_service,
    mock_assignments_service,
    mock_visit_plans_service,
):
    agent1 = Employee(
        phone="1", password_hash="1", full_name="A1", role=EmployeeRole.AGENT
    )
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

    # Wednesday 2026-08-19 (weekday=2): remaining days until Sunday (weekday=6) = 5 days (Wed, Thu, Fri, Sat, Sun)
    with patch("app.application.services.routes_generator.date") as mock_date:
        mock_date.today.return_value = date(2026, 8, 19)
        await service.generate(start=RouteGenerationStart.TODAY)

    assert mock_visit_plans_service.generate_for_employee.await_count == 5


@pytest.mark.asyncio
async def test_generate_start_tomorrow(
    service,
    mock_uow,
    mock_clustering_service,
    mock_assignments_service,
    mock_visit_plans_service,
):
    agent1 = Employee(
        phone="1", password_hash="1", full_name="A1", role=EmployeeRole.AGENT
    )
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

    # Wednesday 2026-08-19 (weekday=2): tomorrow to Sunday = 4 days (Thu, Fri, Sat, Sun)
    with patch("app.application.services.routes_generator.date") as mock_date:
        mock_date.today.return_value = date(2026, 8, 19)
        await service.generate(start=RouteGenerationStart.TOMORROW)

    assert mock_visit_plans_service.generate_for_employee.await_count == 4


def test_get_dates_range_calculations(service):
    # Test Wednesday (weekday=2)
    with patch("app.application.services.routes_generator.date") as mock_date:
        mock_date.today.return_value = date(2026, 8, 19)

        # Today: Wed Aug 19 to Sun Aug 23 (5 days)
        today_dates = service._get_dates_range(RouteGenerationStart.TODAY)
        assert today_dates == [
            date(2026, 8, 19),
            date(2026, 8, 20),
            date(2026, 8, 21),
            date(2026, 8, 22),
            date(2026, 8, 23),
        ]

        # Tomorrow: Thu Aug 20 to Sun Aug 23 (4 days)
        tomorrow_dates = service._get_dates_range(RouteGenerationStart.TOMORROW)
        assert tomorrow_dates == [
            date(2026, 8, 20),
            date(2026, 8, 21),
            date(2026, 8, 22),
            date(2026, 8, 23),
        ]

        # Next week: Mon Aug 24 to Sun Aug 30 (7 days)
        next_week_dates = service._get_dates_range(RouteGenerationStart.NEXT_WEEK)
        assert len(next_week_dates) == 7
        assert next_week_dates[0] == date(2026, 8, 24)
        assert next_week_dates[-1] == date(2026, 8, 30)

    # Test Sunday (weekday=6)
    with patch("app.application.services.routes_generator.date") as mock_date:
        mock_date.today.return_value = date(2026, 8, 23)

        # Today on Sunday: only Sunday
        today_dates = service._get_dates_range(RouteGenerationStart.TODAY)
        assert today_dates == [date(2026, 8, 23)]

        # Tomorrow on Sunday: empty (week ended)
        tomorrow_dates = service._get_dates_range(RouteGenerationStart.TOMORROW)
        assert tomorrow_dates == []

        # Next week on Sunday: Mon Aug 24 to Sun Aug 30
        next_week_dates = service._get_dates_range(RouteGenerationStart.NEXT_WEEK)
        assert len(next_week_dates) == 7
        assert next_week_dates[0] == date(2026, 8, 24)
        assert next_week_dates[-1] == date(2026, 8, 30)


@pytest.mark.asyncio
async def test_clear_all_with_retail_points(
    service,
    mock_uow,
    mock_assignments_service,
):
    point1 = RetailPoint(name="P1", address="A1")
    point2 = RetailPoint(name="P2", address="A2")
    mock_uow.retail_points.list_all.return_value = [point1, point2]

    await service.clear_all()

    mock_assignments_service.clear_employee_assignments.assert_awaited_once_with(
        [point1.id, point2.id]
    )
    mock_uow.visit_plans.delete_all.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_clear_all_without_retail_points(
    service,
    mock_uow,
    mock_assignments_service,
):
    mock_uow.retail_points.list_all.return_value = []

    await service.clear_all()

    mock_assignments_service.clear_employee_assignments.assert_not_awaited()
    mock_uow.visit_plans.delete_all.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()
