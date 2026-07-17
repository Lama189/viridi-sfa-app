from uuid import UUID

from app.domain.entities.retail_points import RetailPoint
from app.domain.entities.users import User
from app.domain.enums import UserRole

from app.application.interfaces.uow import IUnitOfWork
from app.api.v1.schemas.retail_points import CreateRetailPointRequest, UpdateRetailPointRequest


class RetailPointsService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self._uow = uow

    async def create_retail_point(self, dto: CreateRetailPointRequest, agent_id: UUID) -> RetailPoint:
        point = RetailPoint(
                name=dto.name,
                address=dto.address,
                legal_name=dto.legal_name,
                client_type=dto.client_type,
                landmark=dto.landmark,
                contact_person=dto.contact_person,
                phone_number=dto.phone_number,
                inn=dto.inn,
                checking_account=dto.checking_account,
                bank_name=dto.bank_name,
                mfo=dto.mfo,
                oked=dto.oked,
                latitude=dto.latitude,
                longitude=dto.longitude,
                photo_url=dto.photo_url,
                visit_mon=dto.visit_mon,
                visit_tue=dto.visit_tue,
                visit_wed=dto.visit_wed,
                visit_thu=dto.visit_thu,
                visit_fri=dto.visit_fri,
                visit_sat=dto.visit_sat,
                visit_sun=dto.visit_sun,
                created_by_user_id=agent_id,
                is_active=True,
            )
        
        await self._uow.retail_points.add(point)
        await self._uow.commit()
        return point
    
    async def connect_client_to_point(self, point_id: UUID, phone: str, full_name: str) -> None:
        point = await self._uow.retail_points.get_by_id(point_id)
        if not point:
            raise ValueError("Retail point not found")
        
        user = await self._uow.users.get_by_phone(phone=phone)

        if not user:
            user = User(
                phone=phone,
                full_name=full_name,
                role=UserRole.CLIENT,
                telegram_chat_id=None
            )
            
            await self._uow.users.add(user)

        point.owner_user_id = user.id
        await self._uow.retail_points.update(point)

    async def update_retail_point(self, retail_point_id: UUID, dto: UpdateRetailPointRequest) -> RetailPoint:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if not retail_point:
            raise ValueError(f"Retail point {retail_point_id} not found")

        if dto.name is not None:
            retail_point.name = dto.name
        if dto.legal_name is not None:
            retail_point.legal_name = dto.legal_name
        if dto.client_type is not None:
            retail_point.client_type = dto.client_type
        if dto.address is not None:
            retail_point.address = dto.address
        if dto.landmark is not None:
            retail_point.landmark = dto.landmark
        if dto.contact_person is not None:
            retail_point.contact_person = dto.contact_person
        if dto.phone_number is not None:
            retail_point.phone_number = dto.phone_number
        if dto.owner_user_id is not None:
            retail_point.owner_user_id = dto.owner_user_id
        if dto.inn is not None:
            retail_point.inn = dto.inn
        if dto.checking_account is not None:
            retail_point.checking_account = dto.checking_account
        if dto.bank_name is not None:
            retail_point.bank_name = dto.bank_name
        if dto.mfo is not None:
            retail_point.mfo = dto.mfo
        if dto.oked is not None:
            retail_point.oked = dto.oked
        if dto.latitude is not None:
            retail_point.latitude = dto.latitude
        if dto.longitude is not None:
            retail_point.longitude = dto.longitude
        if dto.photo_url is not None:
            retail_point.photo_url = dto.photo_url
        if dto.visit_mon is not None:
            retail_point.visit_mon = dto.visit_mon
        if dto.visit_tue is not None:
            retail_point.visit_tue = dto.visit_tue
        if dto.visit_wed is not None:
            retail_point.visit_wed = dto.visit_wed
        if dto.visit_thu is not None:
            retail_point.visit_thu = dto.visit_thu
        if dto.visit_fri is not None:
            retail_point.visit_fri = dto.visit_fri
        if dto.visit_sat is not None:
            retail_point.visit_sat = dto.visit_sat
        if dto.visit_sun is not None:
            retail_point.visit_sun = dto.visit_sun
        if dto.is_active is not None:
            retail_point.is_active = bool(dto.is_active)

        await self._uow.retail_points.update(retail_point)
        await self._uow.commit()
        return retail_point

    async def delete_retail_point(self, retail_point_id: UUID) -> None:
        retail_point = await self._uow.retail_points.get_by_id(retail_point_id)
        if not retail_point:
            raise ValueError(f"Retail point {retail_point_id} not found")

        await self._uow.retail_points.delete(retail_point)
        await self._uow.commit()

    async def get_by_owner(self, owner_id: UUID, only_active: bool = True) -> list[RetailPoint]:
        return await self._uow.retail_points.list_by_owner(owner_id, only_active)
    
    async def get_by_id(self, retail_point_id: UUID) -> RetailPoint | None:
        return await self._uow.retail_points.get_by_id(retail_point_id)