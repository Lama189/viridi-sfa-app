from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.repos.outbox import IOutboxRepository
from app.domain.entities.outbox_messages import OutboxMessage
from app.infrastructure.postgres.models.outbox_messages import (
    OutboxMessage as OutboxMessageModel,
)


class PostgresOutboxRepository(IOutboxRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: OutboxMessage) -> None:
        model = self._to_model(message)
        self._session.add(model)
        await self._session.flush()

    async def list_unprocessed(
        self,
        limit: int,
    ) -> list[OutboxMessage]:
        stmt = (
            select(OutboxMessageModel)
            .where(OutboxMessageModel.processed_at.is_(None))
            .order_by(OutboxMessageModel.created_at.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def mark_processed(
        self,
        message_id: UUID,
    ) -> None:
        stmt = (
            update(OutboxMessageModel)
            .where(OutboxMessageModel.id == message_id)
            .values(processed_at=datetime.now(timezone.utc))
        )
        await self._session.execute(stmt)
        await self._session.flush()

    def _to_domain(self, model: OutboxMessageModel) -> OutboxMessage:
        return OutboxMessage(
            id=model.id,
            event_type=model.event_type,
            aggregate_type=model.aggregate_type,
            aggregate_id=model.aggregate_id,
            payload=model.payload,
            created_at=model.created_at,
            processed_at=model.processed_at,
        )

    def _to_model(self, message: OutboxMessage) -> OutboxMessageModel:
        return OutboxMessageModel(
            id=message.id,
            event_type=str(message.event_type),
            aggregate_type=str(message.aggregate_type),
            aggregate_id=message.aggregate_id,
            payload=message.payload,
            created_at=message.created_at,
            processed_at=message.processed_at,
        )
