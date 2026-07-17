from uuid import UUID

from sqlalchemy import select, update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces.users import IUserRepository
from app.domain.entities.users import User
from app.infrastructure.postgres.models.users import User as UserModel


class PostgresUserRepository(IUserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> None:
        model = self._to_model(user)
        self._session.add(model)
        await self._session.flush()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def get_by_phone(self, phone: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.phone == phone)
        )

        model = result.scalar_one_or_none()
        if model is None:
            return None

        return self._to_domain(model)

    async def exists_by(self, **kwargs) -> bool:
        stmt = select(select(UserModel).filter_by(**kwargs).exists())
        result = await self._session.execute(stmt)
        return bool(result.scalar())

    async def list_all(self, only_active: bool = True) -> list[User]:
        stmt = select(UserModel)
        if only_active:
            stmt = stmt.where(UserModel.is_active.is_(True))

        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def update(self, user: User) -> None:
        await self._session.execute(
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(
                phone=user.phone,
                full_name=user.full_name,
                role=user.role,
                telegram_chat_id=user.telegram_chat_id,
                is_active=user.is_active,
            )
        )
        await self._session.flush()

    async def delete(self, user: User) -> None:
        await self._session.execute(
            sa_delete(UserModel).where(UserModel.id == user.id)
        )
        await self._session.flush()

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            phone=model.phone,
            full_name=model.full_name,
            role=model.role,
            telegram_chat_id=model.telegram_chat_id,
            is_active=model.is_active,
        )

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            phone=user.phone,
            full_name=user.full_name,
            role=user.role,
            telegram_chat_id=user.telegram_chat_id,
            is_active=user.is_active,
        )
