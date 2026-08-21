from datetime import date, timedelta
from uuid import UUID

from firebase_admin.exceptions import FirebaseError

from app.application.interfaces.services.delivery_assignments import (
    IDeliveryAssignmentService,
)
from app.application.interfaces.services.push_notifications import (
    IPushNotificationService,
)
from app.application.interfaces.uow import IUnitOfWork
from app.core.observability.logging import logger
from app.domain.entities.notifications import Notification
from app.domain.entities.orders import Order
from app.domain.entities.outbox_messages import OutboxMessage
from app.domain.entities.visit_plans import VisitPlan
from app.domain.enums import AggregateType, OrderEventType, OrderStatus


class DeliveryAssignmentService(IDeliveryAssignmentService):
    def __init__(
        self,
        uow: IUnitOfWork,
        push_service: IPushNotificationService | None = None,
        notifications_service: object | None = None,
        min_delivery_days_offset: int = 1,
    ) -> None:
        self._uow = uow
        self._push_service = push_service
        self._notifications_service = notifications_service
        self._min_delivery_days_offset = min_delivery_days_offset

    async def assign_order_to_next_visit(self, order: Order) -> VisitPlan | None:
        if order.status in (
            OrderStatus.LOADED,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.CANCELLED,
        ):
            logger.warning(
                "Order cannot be assigned to visit in its current status",
                order_id=str(order.id),
                status=str(order.status),
            )
            return None

        assignment = await self._uow.retail_point_assignments.get_by_retail_point_id(
            order.retail_point_id
        )
        if not assignment or not assignment.employee_id:
            logger.warning(
                "No agent assigned to retail point for order delivery assignment",
                order_id=str(order.id),
                retail_point_id=str(order.retail_point_id),
            )
            return None

        from_date = date.today() + timedelta(days=self._min_delivery_days_offset)
        next_plan = await self._uow.visit_plans.find_next_plan_for_retail_point(
            employee_id=assignment.employee_id,
            retail_point_id=order.retail_point_id,
            from_date=from_date,
        )
        if not next_plan:
            logger.warning(
                "No upcoming planned visit found for agent and retail point",
                employee_id=str(assignment.employee_id),
                retail_point_id=str(order.retail_point_id),
                order_id=str(order.id),
            )
            return None

        order.planned_visit_id = next_plan.id

        event = OutboxMessage.create(
            event_type=OrderEventType.PLANNED,
            aggregate_type=AggregateType.ORDER,
            aggregate_id=order.id,
            payload={
                "event_type": OrderEventType.PLANNED,
                "order_id": str(order.id),
                "warehouse_id": str(order.warehouse_id),
                "retail_point_id": str(order.retail_point_id),
                "created_by_id": str(order.created_by_id),
                "planned_visit_id": str(order.planned_visit_id),
                "plan_date": str(next_plan.plan_date),
            },
        )
        await self._uow.outbox.add(event)

        point = await self._uow.retail_points.get_by_id(order.retail_point_id)
        point_name = point.name if point else "Торговая точка"

        formatted_date = next_plan.plan_date.strftime("%d.%m.%Y")
        title = "Заказ назначен на ваш визит"
        body = (
            f"Заказ #{str(order.id)[:8]} назначен на визит в торговую точку "
            f"«{point_name}» {formatted_date}."
        )
        push_body = f"Точка «{point_name}», {formatted_date}"

        notification = Notification(
            employee_id=assignment.employee_id,
            title=title,
            body=body,
            notification_type="order_assigned_to_visit",
            payload={
                "order_id": str(order.id),
                "retail_point_id": str(order.retail_point_id),
                "retail_point_name": point_name,
                "planned_visit_id": str(next_plan.id),
                "plan_date": str(next_plan.plan_date),
                "total_amount": float(order.total_amount),
                "total_volume": float(order.total_volume),
                "notification_type": "order_assigned_to_visit",
            },
        )
        await self._uow.notifications.add(notification)

        logger.info(
            "Order assigned notification created for agent",
            employee_id=str(assignment.employee_id),
            order_id=str(order.id),
            notification_id=str(notification.id),
        )

        if self._push_service:
            try:
                await self._push_service.send_to_employee(
                    employee_id=assignment.employee_id,
                    title=title,
                    body=push_body,
                    data={
                        "order_id": str(order.id),
                        "retail_point_id": str(order.retail_point_id),
                        "retail_point_name": point_name,
                        "planned_visit_id": str(next_plan.id),
                        "plan_date": str(next_plan.plan_date),
                        "total_amount": str(order.total_amount),
                        "total_volume": str(order.total_volume),
                        "notification_type": "order_assigned_to_visit",
                    },
                )
            except (
                FirebaseError,
                ConnectionError,
                TimeoutError,
                OSError,
                ValueError,
            ) as exc:
                logger.warning(
                    "Failed to send push notification for assigned order",
                    employee_id=str(assignment.employee_id),
                    order_id=str(order.id),
                    error=str(exc),
                )

        return next_plan

    async def assign_order_by_id(self, order_id: UUID) -> VisitPlan | None:
        order = await self._uow.orders.get_by_id(order_id)
        if not order:
            logger.warning(
                "Order not found for delivery assignment",
                order_id=str(order_id),
            )
            return None

        result = await self.assign_order_to_next_visit(order)
        if result:
            await self._uow.orders.update(order)
        return result
