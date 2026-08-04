from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.application.services.members import RetailPointMembersService
from app.core.exceptions import (
    UserNotFoundError,
    UserNotActiveError,
    MembershipAlreadyExistsError,
    MembershipNotFoundError,
    RetailPointNotFoundError,
    RetailPointInactiveError,
)
from app.domain.entities.clients import Client
from app.domain.entities.retail_point_members import RetailPointMember
from app.domain.entities.retail_points import RetailPoint


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.clients = AsyncMock()
    uow.retail_point_members = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def mock_invite_codes():
    return AsyncMock()


@pytest.fixture
def service(mock_uow, mock_invite_codes):
    return RetailPointMembersService(mock_uow, mock_invite_codes)


# --- join ---

@pytest.mark.asyncio
async def test_join_success(service, mock_uow):
    rp_id = uuid4()
    client_id = uuid4()
    mock_uow.clients.get_by_id.return_value = Client(phone="+998901111111", full_name="C", id=client_id, is_active=True)
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(name="R", address="A", id=rp_id, is_active=True)
    mock_uow.retail_point_members.exists.return_value = False

    result = await service.join(rp_id, client_id)

    assert result.retail_point_id == rp_id
    assert result.client_id == client_id
    mock_uow.retail_point_members.add.assert_awaited_once()


@pytest.mark.asyncio
async def test_join_client_not_found(service, mock_uow):
    mock_uow.clients.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await service.join(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_join_client_not_active(service, mock_uow):
    client_id = uuid4()
    mock_uow.clients.get_by_id.return_value = Client(
        phone="+998901111111", full_name="C", id=client_id, is_active=False,
    )

    with pytest.raises(UserNotActiveError):
        await service.join(uuid4(), client_id)


@pytest.mark.asyncio
async def test_join_retail_point_not_found(service, mock_uow):
    client_id = uuid4()
    mock_uow.clients.get_by_id.return_value = Client(
        phone="+998901111111", full_name="C", id=client_id, is_active=True,
    )
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.join(uuid4(), client_id)


@pytest.mark.asyncio
async def test_join_retail_point_inactive(service, mock_uow):
    rp_id = uuid4()
    client_id = uuid4()
    mock_uow.clients.get_by_id.return_value = Client(
        phone="+998901111111", full_name="C", id=client_id, is_active=True,
    )
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="R", address="A", id=rp_id, is_active=False,
    )

    with pytest.raises(RetailPointInactiveError):
        await service.join(rp_id, client_id)


@pytest.mark.asyncio
async def test_join_already_member(service, mock_uow):
    rp_id = uuid4()
    client_id = uuid4()
    mock_uow.clients.get_by_id.return_value = Client(
        phone="+998901111111", full_name="C", id=client_id, is_active=True,
    )
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="R", address="A", id=rp_id, is_active=True,
    )
    mock_uow.retail_point_members.exists.return_value = True

    with pytest.raises(MembershipAlreadyExistsError):
        await service.join(rp_id, client_id)


# --- leave ---

@pytest.mark.asyncio
async def test_leave_success(service, mock_uow):
    rp_id = uuid4()
    client_id = uuid4()
    membership = RetailPointMember(rp_id, client_id)
    mock_uow.retail_point_members.get_by_retail_point_and_client.return_value = membership

    result = await service.leave(rp_id, client_id)

    assert result.retail_point_id == rp_id
    assert result.client_id == client_id
    mock_uow.retail_point_members.delete.assert_awaited_once_with(membership)


@pytest.mark.asyncio
async def test_leave_not_found(service, mock_uow):
    mock_uow.retail_point_members.get_by_retail_point_and_client.return_value = None

    with pytest.raises(MembershipNotFoundError):
        await service.leave(uuid4(), uuid4())


# --- remove ---

@pytest.mark.asyncio
async def test_remove_success(service, mock_uow):
    rp_id = uuid4()
    client_id = uuid4()
    membership = RetailPointMember(rp_id, client_id)
    mock_uow.retail_point_members.get_by_retail_point_and_client.return_value = membership

    result = await service.remove(rp_id, client_id)

    assert result.retail_point_id == rp_id
    mock_uow.retail_point_members.delete.assert_awaited_once_with(membership)


@pytest.mark.asyncio
async def test_remove_not_found(service, mock_uow):
    mock_uow.retail_point_members.get_by_retail_point_and_client.return_value = None

    with pytest.raises(MembershipNotFoundError):
        await service.remove(uuid4(), uuid4())


# --- get_member ---

@pytest.mark.asyncio
async def test_get_member_success(service, mock_uow):
    rp_id = uuid4()
    client_id = uuid4()
    membership = RetailPointMember(rp_id, client_id)
    mock_uow.retail_point_members.get_by_retail_point_and_client.return_value = membership

    result = await service.get_member(rp_id, client_id)
    assert result.retail_point_id == rp_id
    assert result.client_id == client_id


@pytest.mark.asyncio
async def test_get_member_not_found(service, mock_uow):
    mock_uow.retail_point_members.get_by_retail_point_and_client.return_value = None

    with pytest.raises(MembershipNotFoundError):
        await service.get_member(uuid4(), uuid4())


# --- list_members ---

@pytest.mark.asyncio
async def test_list_members_success(service, mock_uow):
    rp_id = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="R", address="A", id=rp_id, is_active=True,
    )
    members = [
        RetailPointMember(rp_id, uuid4()),
        RetailPointMember(rp_id, uuid4()),
    ]
    mock_uow.retail_point_members.get_by_retail_point.return_value = members

    result = await service.list_members(rp_id)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_members_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.list_members(uuid4())


@pytest.mark.asyncio
async def test_list_members_retail_point_inactive(service, mock_uow):
    rp_id = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="R", address="A", id=rp_id, is_active=False,
    )

    with pytest.raises(RetailPointInactiveError):
        await service.list_members(rp_id)


# --- is_member ---

@pytest.mark.asyncio
async def test_is_member_true(service, mock_uow):
    mock_uow.retail_point_members.exists.return_value = True

    result = await service.is_member(uuid4(), uuid4())
    assert result is True


@pytest.mark.asyncio
async def test_is_member_false(service, mock_uow):
    mock_uow.retail_point_members.exists.return_value = False

    result = await service.is_member(uuid4(), uuid4())
    assert result is False


# --- get_by_telegram ---

@pytest.mark.asyncio
async def test_get_by_telegram_success(service, mock_uow):
    rp_id = uuid4()
    client_id = uuid4()
    membership = RetailPointMember(rp_id, client_id)
    mock_uow.retail_point_members.get_by_telegram_id.return_value = membership

    result = await service.get_by_telegram(123456789)
    assert result.retail_point_id == rp_id
    assert result.client_id == client_id


@pytest.mark.asyncio
async def test_get_by_telegram_not_found(service, mock_uow):
    mock_uow.retail_point_members.get_by_telegram_id.return_value = None

    with pytest.raises(MembershipNotFoundError):
        await service.get_by_telegram(999999)
