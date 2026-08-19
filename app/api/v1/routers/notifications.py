from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import (
    get_current_employee,
    get_notifications_service,
)
from app.api.v1.schemas.notifications import (
    NotificationResponse,
    UnreadCountResponse,
)
from app.application.services.notifications import NotificationsService
from app.core.exceptions import NotificationNotFoundError
from app.domain.entities.auth import AuthenticatedEmployee

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=list[NotificationResponse],
    status_code=status.HTTP_200_OK,
)
async def list_notifications(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[NotificationsService, Depends(get_notifications_service)],
    only_unread: bool = Query(default=False, description="Filter only unread notifications"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    notifications = await service.list_by_employee(
        employee_id=employee.id,
        only_unread=only_unread,
        limit=limit,
        offset=offset,
    )
    return notifications


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    status_code=status.HTTP_200_OK,
)
async def get_unread_notifications_count(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[NotificationsService, Depends(get_notifications_service)],
):
    count = await service.count_unread_by_employee(employee.id)
    return UnreadCountResponse(unread_count=count)


@router.post(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def mark_notification_as_read(
    notification_id: UUID,
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[NotificationsService, Depends(get_notifications_service)],
):
    try:
        notification = await service.get_by_id(notification_id)
        if notification.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this notification",
            )
        return await service.mark_as_read(notification_id)
    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )


@router.post(
    "/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def mark_all_notifications_as_read(
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[NotificationsService, Depends(get_notifications_service)],
):
    await service.mark_all_as_read(employee.id)


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_notification(
    notification_id: UUID,
    employee: Annotated[AuthenticatedEmployee, Depends(get_current_employee)],
    service: Annotated[NotificationsService, Depends(get_notifications_service)],
):
    try:
        notification = await service.get_by_id(notification_id)
        if notification.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this notification",
            )
        await service.delete(notification_id)
    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
