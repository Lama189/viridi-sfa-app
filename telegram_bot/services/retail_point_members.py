from dataclasses import dataclass
from uuid import UUID

from aiohttp import ClientError, ClientSession, ClientTimeout


@dataclass(slots=True)
class RetailPointMemberDTO:
    id: UUID
    retail_point_id: UUID
    client_id: UUID


class RetailPointMembersService:
    def __init__(self, api_url: str) -> None:
        self._api_url = api_url.rstrip("/")

    async def list_members(self, retail_point_id: UUID) -> list[RetailPointMemberDTO]:
        try:
            async with (
                ClientSession(timeout=ClientTimeout(total=10)) as session,
                session.get(
                    f"{self._api_url}/api/v1/retail_points/{retail_point_id}/members"
                ) as response,
            ):
                if response.status != 200:
                    return []
                data = await response.json()
                return [
                    RetailPointMemberDTO(
                        id=UUID(item["id"]),
                        retail_point_id=UUID(item["retail_point_id"]),
                        client_id=UUID(item["client_id"]),
                    )
                    for item in data
                ]
        except ClientError, ValueError, KeyError:
            return []
