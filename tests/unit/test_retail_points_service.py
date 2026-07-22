from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.v1.schemas.retail_points import CreateRetailPointRequest, UpdateRetailPointRequest
from app.application.services.retail_points import RetailPointsService
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
def service(mock_uow, mock_invite_codes):
    return RetailPointsService(mock_uow, mock_invite_codes)


# --- create_retail_point ---

@pytest.mark.asyncio
async def test_create_retail_point_success(service, mock_uow, mock_invite_codes):
    agent_id = uuid4()
    mock_invite_codes.create.return_value="invite-raw-code"
    dto = CreateRetailPointRequest(name="Store-1", address="ul. Test 1")

    point, code = await service.create_retail_point(dto, agent_id)

    assert point.name == "Store-1"
    assert point.address == "ul. Test 1"
    assert point.created_by_employee_id == agent_id
    assert point.is_active is True
    assert code == "invite-raw-code"
    mock_uow.retail_points.add.assert_awaited_once()
    mock_invite_codes.create.assert_awaited_once_with(agent_id, point.id)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_retail_point_with_optional_fields(service, mock_uow, mock_invite_codes):
    agent_id = uuid4()
    mock_invite_codes.create.return_value = "code"
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
        visit_mon=True,
        visit_wed=True,
        visit_fri=True,
    )

    point, _ = await service.create_retail_point(dto, agent_id)

    assert point.legal_name == "OOO Test"
    assert point.client_type == ClientType.B
    assert point.landmark == "near park"
    assert point.inn == "123456789"
    assert point.latitude == Decimal("41.311081")
    assert point.visit_mon is True
    assert point.visit_wed is True
    assert point.visit_fri is True
    assert point.visit_tue is False


# --- get_by_id ---

@pytest.mark.asyncio
async def test_get_by_id_found(service, mock_uow):
    uid = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="X", address="Addr", id=uid,
    )

    result = await service.get_by_id(uid)
    assert result is not None
    assert result.name == "X"


@pytest.mark.asyncio
async def test_get_by_id_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    result = await service.get_by_id(uuid4())
    assert result is None


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
async def test_update_retail_point_visit_schedule(service, mock_uow):
    uid = uuid4()
    point = RetailPoint(name="X", address="A", id=uid, visit_mon=False)
    mock_uow.retail_points.get_by_id.return_value = point

    dto = UpdateRetailPointRequest(visit_mon=True, visit_sun=True)
    result = await service.update_retail_point(uid, dto)

    assert result.visit_mon is True
    assert result.visit_sun is True


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
        name="Del", address="D", id=uid,
    )

    await service.delete_retail_point(uid)

    mock_uow.retail_points.delete.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(ValueError, match="not found"):
        await service.delete_retail_point(uuid4())

    mock_uow.retail_points.delete.assert_not_awaited()
