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
from app.domain.enums import EmployeeRole, OrderStatus, RouteGenerationStart


class RouteGenerationService(IRouteGenerationService):
    def __init__(
        self,
        uow: IUnitOfWork,
        clustering_service: ITerritoryClusteringService,
        assignments_service: IRetailPointAssignmentService,
        visit_plans_service: IVisitPlanService,
        min_delivery_days_offset: int = 1,
    ) -> None:
        self._uow = uow
        self._clustering_service = clustering_service
        self._assignments_service = assignments_service
        self._visit_plans_service = visit_plans_service
        self._min_delivery_days_offset = min_delivery_days_offset

    async def generate(
        self, start: RouteGenerationStart = RouteGenerationStart.NEXT_WEEK
    ) -> None:
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
            start=start,
        )

        await self._replan_unloaded_orders()

        await self._uow.commit()

    async def clear_all(self) -> None:
        retail_points = await self._uow.retail_points.list_all()
        if retail_points:
            await self._assignments_service.clear_employee_assignments(
                [point.id for point in retail_points]
            )

        await self._uow.visit_plans.delete_all()

        unloaded_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.ASSEMBLY_STARTED,
            OrderStatus.ASSEMBLED,
        ]
        orders = await self._uow.orders.list(statuses=unloaded_statuses, limit=1000)
        for order in orders:
            if order.planned_visit_id is not None:
                order.planned_visit_id = None
                await self._uow.orders.update(order)

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
        start: RouteGenerationStart = RouteGenerationStart.NEXT_WEEK,
    ) -> None:
        week_dates = self._get_dates_range(start)

        for agent in agents:
            for plan_date in week_dates:
                await self._visit_plans_service.generate_for_employee(
                    employee_id=agent.id,
                    plan_date=plan_date,
                )

    async def _replan_unloaded_orders(self) -> None:
        unloaded_statuses = [
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.ASSEMBLY_STARTED,
            OrderStatus.ASSEMBLED,
        ]
        orders = await self._uow.orders.list(statuses=unloaded_statuses, limit=1000)

        for order in orders:
            assignment = (
                await self._uow.retail_point_assignments.get_by_retail_point_id(
                    order.retail_point_id
                )
            )
            new_planned_visit_id = None
            if assignment and assignment.employee_id:
                from_date = date.today() + timedelta(
                    days=self._min_delivery_days_offset
                )
                next_plan = await self._uow.visit_plans.find_next_plan_for_retail_point(
                    employee_id=assignment.employee_id,
                    retail_point_id=order.retail_point_id,
                    from_date=from_date,
                )
                if next_plan:
                    new_planned_visit_id = next_plan.id

            if order.planned_visit_id != new_planned_visit_id:
                order.planned_visit_id = new_planned_visit_id
                await self._uow.orders.update(order)

    def _get_dates_range(self, start: RouteGenerationStart) -> list[date]:
        today = date.today()

        if start == RouteGenerationStart.TODAY:
            days_until_sunday = 6 - today.weekday()
            return [today + timedelta(days=i) for i in range(days_until_sunday + 1)]

        if start == RouteGenerationStart.TOMORROW:
            days_until_sunday = 6 - today.weekday()
            if days_until_sunday < 1:
                return []
            tomorrow = today + timedelta(days=1)
            return [tomorrow + timedelta(days=i) for i in range(days_until_sunday)]

        days_until_next_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_next_monday)
        return [next_monday + timedelta(days=i) for i in range(7)]
