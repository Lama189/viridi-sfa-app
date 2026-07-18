from uuid import UUID

from app.domain.entities.users import User

from app.application.interfaces.uow import IUnitOfWork
from app.api.v1.schemas.users import UserCreate, UserUpdate


class UsersService:

    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_user(self, dto: UserCreate) -> User:
        if await self._uow.users.exists_by(phone=dto.phone):
            raise ValueError(f"A user with phone number '{dto.phone}' already exists.")

        user = User(
            phone=dto.phone,
            full_name=dto.full_name,
            role=dto.role,
            telegram_chat_id=dto.telegram_chat_id,
        )

        await self._uow.users.add(user)
        await self._uow.commit()
        return user

    async def get_user(self, user_id: UUID) -> User | None:
        return await self._uow.users.get_by_id(user_id)

    async def get_user_by_phone(self, phone: str) -> User | None:
        return await self._uow.users.get_by_phone(phone)

    async def list_users(self, only_active: bool = True) -> list[User]:
        return await self._uow.users.list_all(only_active)

    async def update_user(self, user_id: UUID, dto: UserUpdate) -> User:
        user = await self._uow.users.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        if dto.phone is not None:
            existing = await self._uow.users.get_by_phone(dto.phone)
            if existing and existing.id != user_id:
                raise ValueError(f"Phone '{dto.phone}' is already in use")
            user.phone = dto.phone

        if dto.full_name is not None:
            user.full_name = dto.full_name

        if dto.role is not None:
            user.role = dto.role

        if dto.telegram_chat_id is not None:
            user.telegram_chat_id = dto.telegram_chat_id

        if dto.is_active is not None:
            user.is_active = bool(dto.is_active)

        await self._uow.users.update(user)
        await self._uow.commit()
        return user

    async def delete_user(self, user_id: UUID) -> None:
        user = await self._uow.users.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        await self._uow.users.delete(user)
        await self._uow.commit()
