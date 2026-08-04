from dataclasses import dataclass
from uuid import UUID

from aiohttp import ClientError, ClientSession, ClientTimeout


@dataclass(slots=True)
class ClientDTO:
    id: UUID
    phone: str
    full_name: str
    telegram_id: int | None


class ClientsService:
    def __init__(self, api_url: str) -> None:
        self._api_url = api_url.rstrip("/")

    async def get(self, client_id: UUID) -> ClientDTO | None:
        try:
            async with (
                ClientSession(timeout=ClientTimeout(total=10)) as session,
                session.get(f"{self._api_url}/api/v1/clients/{client_id}") as response,
            ):
                if response.status != 200:
                    return None
                data = await response.json()
                return ClientDTO(
                    id=UUID(data["id"]),
                    phone=data.get("phone", ""),
                    full_name=data.get("full_name", ""),
                    telegram_id=data.get("telegram_chat_id"),
                )
        except ClientError, ValueError, KeyError:
            return None

    get_client = get
