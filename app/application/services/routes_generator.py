from datetime import date, timedelta

from app.application.interfaces.services.retail_point_assignments import (
    IRetailPointAssignmentService,
)
from app.application.interfaces.services.routes_generator import IRouteGenerationService
from app.application.interfaces.services.territories import ITerritoryClusteringService
from app.application.interfaces.services.visit_plans import IVisitPlanService
from app.application.interfaces.uow import IUnitOfWork
from app.core.exceptions import (
    NoActiveAgentsFoundError,
    NoActiveRetailPointsError,
    TerritoryClustersNotBuiltError,
)
from app.domain.entities.employees import Employee
from app.domain.entities.territories import TerritoryCluster
from app.domain.enums import EmployeeRole


class RouteGenerationService(IRouteGenerationService):
    def __init__(
        self,
        uow: IUnitOfWork,
        clustering_service: ITerritoryClusteringService,
        assignments_service: IRetailPointAssignmentService,
        visit_plans_service: IVisitPlanService,
    ) -> None:
        self._uow = uow
        self._clustering_service = clustering_service
        self._assignments_service = assignments_service
        self._visit_plans_service = visit_plans_service

    async def generate(self) -> None:
        agents = await self._uow.employees.list_by(
            role=EmployeeRole.AGENT,
            is_active=True,
        )
        if not agents:
            raise NoActiveAgentsFoundError()

        retail_points = await self._uow.retail_points.list_all()
        if not retail_points:
            raise NoActiveRetailPointsError()

        clusters = await self._clustering_service.build_clusters(
            retail_points,
            len(agents),
        )

        if not clusters:
            raise TerritoryClustersNotBuiltError()

        await self._assignments_service.clear_employee_assignments(
            [point.id for point in retail_points]
        )

        assigned_agents = await self._assign_clusters(
            clusters,
            agents,
        )

        await self._generate_visit_plans(
            assigned_agents,
        )

        await self._uow.commit()

    async def _assign_clusters(
        self,
        clusters: list[TerritoryCluster],
        agents: list[Employee],
    ) -> list[Employee]:
        assigned_agents: list[Employee] = []

        for cluster, agent in zip(clusters, agents):
            assigned_agents.append(agent)

            for retail_point in cluster.retail_points:
                await self._assignments_service.assign_employee(
                    retail_point_id=retail_point.id,
                    employee_id=agent.id,
                )

        return assigned_agents

    async def _generate_visit_plans(
        self,
        agents: list[Employee],
    ) -> None:
        week_dates = self._get_next_week_dates()

        for agent in agents:
            for plan_date in week_dates:
                await self._visit_plans_service.generate_for_employee(
                    employee_id=agent.id,
                    plan_date=plan_date,
                )

    def _get_next_week_dates(self) -> list[date]:
        today = date.today()

        days_until_next_monday = 7 - today.weekday()

        next_monday = today + timedelta(days=days_until_next_monday)

        return [next_monday + timedelta(days=i) for i in range(7)]
