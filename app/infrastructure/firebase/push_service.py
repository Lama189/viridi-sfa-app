from uuid import UUID

from firebase_admin import messaging
from firebase_admin.exceptions import FirebaseError

from app.application.interfaces.services.push_notifications import (
    IPushNotificationService,
)
from app.application.interfaces.uow import IUnitOfWork
from app.core.observability.logging import logger
from app.infrastructure.firebase.client import get_messaging


class FirebasePushNotificationService(IPushNotificationService):

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def send_to_employee(
        self,
        employee_id: UUID,
        title: str,
        body: str,
        data: dict[str, str] | None = None,
    ) -> int:
        devices = await self._uow.employee_devices.list_by_employee(employee_id)
        if not devices:
            logger.info(
                "No registered devices for employee push",
                employee_id=str(employee_id),
            )
            return 0

        tokens_map = {
            device.fcm_token: device
            for device in devices
            if device.fcm_token
        }
        tokens = list(tokens_map.keys())

        if not tokens:
            return 0

        fb_messaging = get_messaging()

        if fb_messaging is None:
            logger.info(
                "Push notifications mock mode enabled. Skipping actual dispatch",
                employee_id=str(employee_id),
                device_count=len(tokens),
                title=title,
            )
            return len(tokens)

        payload_data = ({k: str(v) for k, v in data.items()} if data else {})

        message = fb_messaging.MulticastMessage(
            notification=fb_messaging.Notification(
                title=title,
                body=body,
            ),
            data=payload_data,
            tokens=tokens,
        )

        try:
            response: messaging.BatchResponse = (fb_messaging.send_each_for_multicast(message))

            logger.info(
                "Multicast push notification executed",
                employee_id=str(employee_id),
                success_count=response.success_count,
                failure_count=response.failure_count,
            )

            if response.failure_count > 0:
                await self._handle_failed_tokens(
                    tokens=tokens,
                    responses=response.responses,
                )

            return response.success_count

        except FirebaseError as e:
            logger.error(
                "Failed to send multicast push via Firebase",
                employee_id=str(employee_id),
                error=str(e),
            )
            return 0


    async def _handle_failed_tokens(
        self,
        tokens: list[str],
        responses: list[messaging.SendResponse]
    ) -> None:
        invalid_tokens: list[str] = []
        
        for token, resp in zip(tokens, responses, strict=True):
            if not resp.success and resp.exception:
                error_code = resp.exception.code

                if error_code in ("UNREGISTERED", "INVALID_ARGUMENT"):
                    invalid_tokens.append(token)

        if invalid_tokens:
            logger.info(
                "Removing stale/unregistered FCM tokens from database",
                count=len(invalid_tokens),
            )
            async with self._uow:
                await self._uow.employee_devices.delete_by_tokens(
                    invalid_tokens
                )
                await self._uow.commit()