from uuid import UUID

from app.core.observability.logging import logger
from app.application.interfaces.uow import IUnitOfWork
from app.application.interfaces.services.retail_point_assignments import IRetailPointAssignmentService
from app.domain.entities.retail_point_assignments import RetailPointAssignment
from app.core.extensions import (
    RetailPointNotFoundError,
    RetailPointInactiveError,
    RetailPointAssignmentNotFoundError,
    RetailPointAssignmentAlreadyExistsError,
    UserNotFoundError,
    UserNotActiveError
)
from app.core.observability.metrics import retail_point_assignment_operations_total


class RetailPointAssignmentService(IRetailPointAssignmentService):

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def _validate_retail_point(
        self,
        retail_point_id: UUID,
    ) -> None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)

        if retail_point is None:
            logger.warning(
                "Retail point not found during assignment validation",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointNotFoundError()

        if not retail_point.is_active:
            logger.warning(
                "Retail point is inactive during assignment validation",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointInactiveError()

    async def _validate_employee(
        self,
        employee_id: UUID
    ) -> None:
        employee = await self._uow.employees.get_by_id(employee_id)

        if employee is None:
            logger.warning(
                "Employee not found during assignment validation",
                target_employee_id=str(employee_id),
            )
            raise UserNotFoundError()

        if not employee.is_active:
            logger.warning(
                "Employee is inactive during assignment validation",
                target_employee_id=str(employee_id),
            )
            raise UserNotActiveError()

    async def create(
        self,
        retail_point_id: UUID,
    ) -> RetailPointAssignment:
        logger.info(
            "Creating retail point assignment",
            retail_point_id=str(retail_point_id),
        )

        await self._validate_retail_point(retail_point_id)

        if await self._uow.retail_point_assignments.exists_by_retail_point_id(retail_point_id):
            logger.warning(
                "Retail point assignment already exists",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointAssignmentAlreadyExistsError()

        assignment = RetailPointAssignment(
            retail_point_id=retail_point_id,
            employee_id=None
        )
        await self._uow.retail_point_assignments.add(assignment)
        retail_point_assignment_operations_total.labels(action="create").inc()

        logger.info(
            "Retail point assignment successfully created",
            retail_point_id=str(retail_point_id),
        )

        return assignment

    async def delete(
        self,
        retail_point_id: UUID
    ) -> None:
        logger.info(
            "Deleting retail point assignment",
            retail_point_id=str(retail_point_id),
        )

        await self._validate_retail_point(retail_point_id)

        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(retail_point_id)
        if assignment is None:
            logger.warning(
                "Retail point assignment not found for deletion",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointAssignmentNotFoundError()

        await self._uow.retail_point_assignments.delete(assignment)
        retail_point_assignment_operations_total.labels(action="delete").inc()

        logger.info(
            "Retail point assignment successfully deleted",
            retail_point_id=str(retail_point_id),
        )

    async def assign_employee(
        self,
        retail_point_id: UUID,
        employee_id: UUID
    ) -> RetailPointAssignment:
        logger.info(
            "Assigning employee to retail point",
            retail_point_id=str(retail_point_id),
            target_employee_id=str(employee_id),
        )

        await self._validate_retail_point(retail_point_id)
        await self._validate_employee(employee_id)

        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(retail_point_id)
        if assignment is None:
            logger.warning(
                "Retail point assignment not found",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointAssignmentNotFoundError()

        assignment.assign_employee(employee_id)
        await self._uow.retail_point_assignments.update(assignment)

        await self._uow.commit()
        retail_point_assignment_operations_total.labels(action="assign_employee").inc()

        logger.info(
            "Employee successfully assigned to retail point",
            retail_point_id=str(retail_point_id),
            target_employee_id=str(employee_id),
        )

        return assignment

    async def unassign_employee(
        self,
        retail_point_id: UUID
    ) -> RetailPointAssignment:
        logger.info(
            "Unassigning employee from retail point",
            retail_point_id=str(retail_point_id),
        )

        await self._validate_retail_point(retail_point_id)

        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(retail_point_id)
        if assignment is None:
            logger.warning(
                "Retail point assignment not found for unassigning",
                retail_point_id=str(retail_point_id),
            )
            raise RetailPointAssignmentNotFoundError()

        assignment.remove_employee()
        await self._uow.retail_point_assignments.update(assignment)

        await self._uow.commit()
        retail_point_assignment_operations_total.labels(action="unassign_employee").inc()

        logger.info(
            "Employee successfully unassigned from retail point",
            retail_point_id=str(retail_point_id),
        )

        return assignment

    async def create_many(
        self,
        retail_point_ids: list[UUID]
    ) -> None:
        logger.info(
            "Creating multiple retail point assignments",
            count=len(retail_point_ids),
        )

        assignments_list: list[RetailPointAssignment] = []

        for point_id in retail_point_ids:
            assignment = RetailPointAssignment(
                retail_point_id=point_id,
                employee_id=None
            )

            assignments_list.append(assignment)

        await self._uow.retail_point_assignments.add_many(assignments_list)
        retail_point_assignment_operations_total.labels(
            action="create_many"
        ).inc(len(assignments_list))

        logger.info(
            "Multiple retail point assignments successfully created",
            created_count=len(assignments_list),
        )

    async def clear_employee_assignments(
        self,
        retail_point_ids: list[UUID],
    ) -> None:
        logger.info(
            "Clearing employee assignments for retail points",
            count=len(retail_point_ids),
        )

        await self._uow.retail_point_assignments.clear_employee_assignments(retail_point_ids)
        retail_point_assignment_operations_total.labels(
            action="clear_employee_assignments"
        ).inc(len(retail_point_ids))

        logger.info(
            "Cleared employee assignments for retail points",
            count=len(retail_point_ids),
        )
