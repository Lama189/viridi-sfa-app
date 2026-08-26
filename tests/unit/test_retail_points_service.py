from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.retail_points import (
    CreateRetailPointRequest,
    UpdateRetailPointRequest,
    VisitsDatesDTO,
)
from app.application.services.retail_points import RetailPointsService
from app.core.exceptions import RetailPointNotFoundError
from app.domain.entities.retail_points import RetailPoint
from app.domain.enums import ClientType


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_invite_codes():
    return AsyncMock()


@pytest.fixture
def mock_assignments():
    return AsyncMock()


@pytest.fixture
def mock_visits_rules():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_invite_codes, mock_assignments, mock_visits_rules):
    return RetailPointsService(
        mock_uow,
        mock_invite_codes,
        mock_assignments,
        mock_visits_rules,
    )


# --- create_retail_point ---


@pytest.mark.asyncio
async def test_create_retail_point_success(
    service, mock_uow, mock_invite_codes, mock_visits_rules
):
    agent_id = uuid4()
    mock_invite_codes.create.return_value = "invite-raw-code"
    dto = CreateRetailPointRequest(name="Store-1", address="ul. Test 1")

    point, code = await service.create_retail_point(dto, agent_id)

    assert point.name == "Store-1"
    assert point.address == "ul. Test 1"
    assert point.created_by_employee_id == agent_id
    assert point.is_active is True
    assert code == "invite-raw-code"
    mock_uow.retail_points.add.assert_awaited_once()
    mock_visits_rules.replace_schedule.assert_awaited_once_with(point.id, dto.visits)
    mock_invite_codes.create.assert_awaited_once_with(agent_id, point.id)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_retail_point_with_optional_fields(
    service, mock_uow, mock_invite_codes, mock_visits_rules
):
    agent_id = uuid4()
    mock_invite_codes.create.return_value = "code"
    visits_dto = VisitsDatesDTO(mon=True, wed=True, fri=True)
    dto = CreateRetailPointRequest(
        name="Store-2",
        address="ul. Test 2",
        legal_name="OOO Test",
        client_type=ClientType.B,
        landmark="near park",
        contact_person="John",
        phone_number="+998901234567",
        inn="123456789",
        latitude=Decimal("41.311081"),
        longitude=Decimal("69.240562"),
        visits=visits_dto,
    )

    point, _ = await service.create_retail_point(dto, agent_id)

    assert point.legal_name == "OOO Test"
    assert point.client_type == ClientType.B
    assert point.landmark == "near park"
    assert point.inn == "123456789"
    assert point.latitude == Decimal("41.311081")
    mock_visits_rules.replace_schedule.assert_awaited_once_with(point.id, visits_dto)


# --- get_by_id ---


@pytest.mark.asyncio
async def test_get_by_id_found(service, mock_uow):
    uid = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="X",
        address="Addr",
        id=uid,
    )

    result = await service.get_by_id(uid)
    assert result is not None
    assert result.name == "X"


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.get_by_id(uuid4())


# --- get_details ---


@pytest.mark.asyncio
async def test_get_details_success(service, mock_uow):
    from app.domain.entities.retail_points import RetailPointDetails

    retail_point_id = uuid4()
    retail_point = RetailPoint(
        id=retail_point_id,
        name="Point",
        address="Address",
    )
    orders = [AsyncMock()]
    debts = [AsyncMock()]
    details = RetailPointDetails(
        retail_point=retail_point,
        orders=orders,
        debts=debts,
    )
    mock_uow.retail_points.get_details_by_id.return_value = details

    result = await service.get_details(retail_point_id)

    assert result == details
    mock_uow.retail_points.get_details_by_id.assert_awaited_once_with(retail_point_id)


@pytest.mark.asyncio
async def test_get_details_retail_point_not_found(service, mock_uow):
    retail_point_id = uuid4()
    mock_uow.retail_points.get_details_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.get_details(retail_point_id)

    mock_uow.retail_points.get_details_by_id.assert_awaited_once_with(retail_point_id)


# --- update_retail_point ---


@pytest.mark.asyncio
async def test_update_retail_point_success(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="Old", address="Old Addr", id=uid)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(name="New", address="New Addr")
    result = await service.update_retail_point(uid, dto)

    assert result.name == "New"
    assert result.address == "New Addr"
    mock_uow.retail_points.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_retail_point_partial(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="Keep", address="Keep Addr", id=uid)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(name="Changed")
    result = await service.update_retail_point(uid, dto)

    assert result.name == "Changed"
    assert result.address == "Keep Addr"


@pytest.mark.asyncio
async def test_update_retail_point_visit_schedule(service, mock_uow, mock_visits_rules):
    uid = uuid4()
    point = RetailPoint(name="X", address="A", id=uid)
    mock_uow.retail_points.get_by_id.return_value = point

    visits_dto = VisitsDatesDTO(mon=True, sun=True)
    dto = UpdateRetailPointRequest(visits=visits_dto)
    await service.update_retail_point(uid, dto)

    mock_visits_rules.replace_schedule.assert_awaited_once_with(uid, visits_dto)


@pytest.mark.asyncio
async def test_update_retail_point_toggle_active(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="X", address="A", id=uid, is_active=True)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(is_active=False)
    result = await service.update_retail_point(uid, dto)

    assert result.is_active is False


@pytest.mark.asyncio
async def test_update_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    dto = UpdateRetailPointRequest(name="X")
    with pytest.raises(ValueError, match="not found"):
        await service.update_retail_point(uuid4(), dto)


# --- delete_retail_point ---


@pytest.mark.asyncio
async def test_delete_retail_point_success(service, mock_uow):
    uid = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="Del",
        address="D",
        id=uid,
    )

    await service.delete_retail_point(uid)

    mock_uow.retail_points.delete.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.delete_retail_point(uuid4())

    mock_uow.retail_points.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_list_by_employee_and_weekday_success(service, mock_uow):
    from app.domain.enums import Weekday

    emp_id = uuid4()
    point = RetailPoint(id=uuid4(), name="Mon Point", address="Addr 1")
    mock_uow.retail_points.list_by_employee_and_weekday.return_value = [point]

    result = await service.list_by_employee_and_weekday(emp_id, Weekday.MONDAY)

    assert len(result) == 1
    assert result[0].name == "Mon Point"
    mock_uow.retail_points.list_by_employee_and_weekday.assert_awaited_once_with(
        employee_id=emp_id,
        weekday=Weekday.MONDAY,
        only_active=True,
    )


@pytest.mark.asyncio
async def test_list_debtors_as_agent(service, mock_uow):
    from app.application.dto.retail_points import (
        RetailPointDebtorDTO,
        RetailPointShortDTO,
    )
    from app.domain.entities.visit_debts import VisitDebt
    from app.domain.enums import EmployeeRole

    agent_id = uuid4()
    point_id = uuid4()
    debt = VisitDebt(visit_id=uuid4(), amount=Decimal("50000.00"), comment="Unpaid")
    debtor_dto = RetailPointDebtorDTO(
        retail_point=RetailPointShortDTO(
            id=point_id, name="Debtor 1", address="Addr 1"
        ),
        total_debt=Decimal("50000.00"),
        debts_count=1,
        debts=[debt],
    )
    mock_uow.retail_points.list_debtors.return_value = [debtor_dto]

    result = await service.list_debtors(
        employee_id=agent_id,
        role=EmployeeRole.AGENT,
        limit=50,
        offset=0,
    )

    assert len(result) == 1
    assert result[0].total_debt == Decimal("50000.00")
    assert result[0].retail_point.name == "Debtor 1"
    mock_uow.retail_points.list_debtors.assert_awaited_once_with(
        employee_id=agent_id,
        limit=50,
        offset=0,
    )


@pytest.mark.asyncio
async def test_list_debtors_as_admin(service, mock_uow):
    from app.domain.enums import EmployeeRole

    admin_id = uuid4()
    mock_uow.retail_points.list_debtors.return_value = []

    result = await service.list_debtors(
        employee_id=admin_id,
        role=EmployeeRole.ADMIN,
        filter_employee_id=None,
        limit=20,
        offset=0,
    )

    assert result == []
    mock_uow.retail_points.list_debtors.assert_awaited_once_with(
        employee_id=None,
        limit=20,
        offset=0,
    )
