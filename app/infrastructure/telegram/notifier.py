from aiohttp import ClientError, ClientSession, ClientTimeout

from app.core.config import get_settings
from app.core.observability.logging import logger


async def send_telegram_notification(
    chat_id: int | None,
    text: str,
    token: str | None = None,
) -> None:
    bot_token = token or get_settings().telegram_bot_token
    if not bot_token or not chat_id or not isinstance(chat_id, int):
        return
    try:
        async with ClientSession(timeout=ClientTimeout(total=5.0)) as session:
            session.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                },
            )
    except (ClientError, OSError) as exc:
        logger.warning(
            "Failed to send telegram notification",
            chat_id=chat_id,
            error=str(exc),
        )
