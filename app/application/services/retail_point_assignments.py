from uuid import UUID

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


class RetailPointAssignmentService(IRetailPointAssignmentService):

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def _validate_retail_point(
        self,
        retail_point_id: UUID,
    ) -> None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        
        if retail_point is None:
            raise RetailPointNotFoundError()
    
        if not retail_point.is_active:
            raise RetailPointInactiveError()

    async def _validate_employee(
        self, 
        employee_id: UUID
    ) -> None:
        employee = await self._uow.employees.get_by_id(employee_id)

        if employee is None:
            raise UserNotFoundError()

        if not employee.is_active:
            raise UserNotActiveError()

    async def create(
        self,
        retail_point_id: UUID,
    ) -> RetailPointAssignment:
        await self._validate_retail_point(retail_point_id)

        if await self._uow.retail_point_assignments.exists_by_retail_point_id(retail_point_id):
            raise RetailPointAssignmentAlreadyExistsError()

        assignment = RetailPointAssignment(
            retail_point_id=retail_point_id,
            employee_id=None
        )
        await self._uow.retail_point_assignments.add(assignment)

        return assignment

    async def delete(
        self,
        retail_point_id: UUID
    ) -> None:
        await self._validate_retail_point(retail_point_id)

        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(retail_point_id)
        if assignment is None:
            raise RetailPointAssignmentNotFoundError()

        await self._uow.retail_point_assignments.delete(assignment)

    async def assign_employee(
        self,
        retail_point_id: UUID,
        employee_id: UUID
    ) -> RetailPointAssignment:
        await self._validate_retail_point(retail_point_id)
        await self._validate_employee(employee_id)

        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(retail_point_id)
        if assignment is None:
            raise RetailPointAssignmentNotFoundError()
        
        await self._uow.retail_point_assignments.update(assignment)

        await self._uow.commit()

        return assignment

    async def unassign_employee(
        self,
        retail_point_id: UUID
    ) -> RetailPointAssignment:
        await self._validate_retail_point(retail_point_id)
        
        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(retail_point_id)
        if assignment is None:
            raise RetailPointAssignmentNotFoundError()

        assignment.remove_employee()
        await self._uow.retail_point_assignments.update(assignment)
        
        await self._uow.commit()
        
        return assignment