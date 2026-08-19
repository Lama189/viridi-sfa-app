from datetime import date
from uuid import UUID

from app.application.dto.notifications import NotificationCreateDTO
from app.application.interfaces.services.delivery_proposals import (
    IDeliveryProposalService,
)
from app.application.interfaces.services.notifications import INotificationsService
from app.application.interfaces.uow import IUnitOfWork
from app.core.observability.logging import logger
from app.domain.entities.notifications import Notification
from app.domain.enums import OrderStatus


class DeliveryProposalService(IDeliveryProposalService):
    def __init__(
        self,
        uow: IUnitOfWork,
        notifications_service: INotificationsService,
    ) -> None:
        self._uow = uow
        self._notifications_service = notifications_service

    async def process_assembled_order(self, order_id: UUID) -> Notification | None:
        order = await self._uow.orders.get_by_id(order_id)
        if not order:
            logger.warning("Order not found for delivery proposal", order_id=str(order_id))
            return None

        if order.status != OrderStatus.ASSEMBLED:
            logger.warning(
                "Order is not in ASSEMBLED status for delivery proposal",
                order_id=str(order_id),
                status=str(order.status),
            )
            return None

        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(order.retail_point_id)
        if not assignment or not assignment.employee_id:
            logger.warning(
                "No agent assigned to retail point for order delivery proposal",
                order_id=str(order_id),
                retail_point_id=str(order.retail_point_id),
            )
            return None

        point = await self._uow.retail_points.get_by_id(order.retail_point_id)
        point_name = point.name if point else "Торговая точка"

        next_plan = await self._uow.visit_plans.find_next_plan_for_retail_point(
            employee_id=assignment.employee_id,
            retail_point_id=order.retail_point_id,
            from_date=date.today(),
        )
        if not next_plan:
            logger.warning(
                "No upcoming planned visit found for agent and retail point",
                employee_id=str(assignment.employee_id),
                retail_point_id=str(order.retail_point_id),
                order_id=str(order_id),
            )
            return None

        formatted_date = next_plan.plan_date.strftime("%d.%m.%Y")
        title = "Заказ готов к доставке"
        body = (
            f"Заказ #{str(order.id)[:8]} ({float(order.total_volume):.2f} м³, "
            f"{float(order.total_amount):,.0f} сум) собран. "
            f"Доставить в точку «{point_name}» {formatted_date}?"
        )

        dto = NotificationCreateDTO(
            employee_id=assignment.employee_id,
            title=title,
            body=body,
            notification_type="order_delivery_proposal",
            payload={
                "order_id": str(order.id),
                "retail_point_id": str(order.retail_point_id),
                "retail_point_name": point_name,
                "visit_plan_id": str(next_plan.id),
                "plan_date": str(next_plan.plan_date),
                "total_amount": float(order.total_amount),
                "total_volume": float(order.total_volume),
            },
        )

        notification = await self._notifications_service.create(dto)
        logger.info(
            "Delivery proposal notification created for agent",
            employee_id=str(assignment.employee_id),
            order_id=str(order.id),
            notification_id=str(notification.id),
        )
        return notification
