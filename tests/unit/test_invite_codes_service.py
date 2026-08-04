from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.application.services.invite_codes import ClientInviteCodesService
from app.core.exceptions import InvalidInviteCodeError, UserNotFoundError, UserNotActiveError, RetailPointNotFoundError, RetailPointInactiveError
from app.domain.entities.employees import Employee
from app.domain.entities.invite_codes import ClientInviteCode
from app.domain.entities.retail_points import RetailPoint


@pytest.fixture
def mock_uow():
    uow = AsyncMock()
    uow.invite_codes = AsyncMock()
    uow.retail_points = AsyncMock()
    uow.employees = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture
def service(mock_uow):
    return ClientInviteCodesService(mock_uow)


# --- create ---

@pytest.mark.asyncio
@patch("app.application.services.invite_codes.SecurityUtils.generate_invite_code", return_value=("raw_code", "encrypted_code", "hash_code"))
async def test_create_success(mock_gen, service, mock_uow):
    rp_id = uuid4()
    emp_id = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(name="X", address="A", id=rp_id)

    result = await service.create(emp_id, rp_id)

    assert result == "raw_code"
    mock_uow.invite_codes.add.assert_awaited_once()
    # Note: commit is NOT called in create (only in regenerate/activate/deactivate)


@pytest.mark.asyncio
async def test_create_retail_point_not_found(service, mock_uow):
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.create(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_create_retail_point_inactive(service, mock_uow):
    rp_id = uuid4()
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(
        name="X", address="A", id=rp_id, is_active=False,
    )

    with pytest.raises(RetailPointInactiveError):
        await service.create(uuid4(), rp_id)


# --- regenerate ---

@pytest.mark.asyncio
@patch("app.application.services.invite_codes.SecurityUtils.generate_invite_code", return_value=("new_raw", "new_encrypted", "new_hash"))
async def test_regenerate_success(mock_gen, service, mock_uow):
    rp_id = uuid4()
    emp_id = uuid4()
    mock_uow.employees.get_by_id.return_value = _make_employee(is_active=True)
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(name="X", address="A", id=rp_id)
    existing = ClientInviteCode(
        retail_point_id=rp_id, encrypted_code="old_encrypted", code_hash="old_hash", created_by_employee_id=emp_id,
    )
    mock_uow.invite_codes.get_by_retail_point.return_value = existing

    result = await service.regenerate(emp_id, rp_id)

    assert result == "new_raw"
    assert existing.encrypted_code == "new_encrypted"
    assert existing.code_hash == "new_hash"
    assert existing.last_activated_client_id is None
    assert existing.last_activated_at is None
    mock_uow.invite_codes.update.assert_awaited_once_with(existing)
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_regenerate_employee_not_found(service, mock_uow):
    mock_uow.employees.get_by_id.return_value = None

    with pytest.raises(UserNotFoundError):
        await service.regenerate(uuid4(), uuid4())


@pytest.mark.asyncio
async def test_regenerate_employee_inactive(service, mock_uow):
    emp_id = uuid4()
    mock_uow.employees.get_by_id.return_value = _make_employee(is_active=False)

    with pytest.raises(UserNotActiveError):
        await service.regenerate(emp_id, uuid4())


@pytest.mark.asyncio
async def test_regenerate_retail_point_not_found(service, mock_uow):
    emp_id = uuid4()
    mock_uow.employees.get_by_id.return_value = _make_employee(is_active=True)
    mock_uow.retail_points.get_by_id.return_value = None

    with pytest.raises(RetailPointNotFoundError):
        await service.regenerate(emp_id, uuid4())


@pytest.mark.asyncio
async def test_regenerate_no_existing_code(service, mock_uow):
    emp_id = uuid4()
    rp_id = uuid4()
    mock_uow.employees.get_by_id.return_value = _make_employee(is_active=True)
    mock_uow.retail_points.get_by_id.return_value = RetailPoint(name="X", address="A", id=rp_id)
    mock_uow.invite_codes.get_by_retail_point.return_value = None

    with pytest.raises(ValueError, match="no invite code"):
        await service.regenerate(emp_id, rp_id)


# --- activate ---

@pytest.mark.asyncio
async def test_activate_success(service, mock_uow):
    client_id = uuid4()
    rp_id = uuid4()
    invite = ClientInviteCode(
        retail_point_id=rp_id, encrypted_code="enc", code_hash="hash", created_by_employee_id=uuid4(),
    )
    mock_uow.invite_codes.get_by_code_hash.return_value = invite

    with patch("app.application.services.invite_codes.SecurityUtils.hash_invite_code", return_value="hash"):
        result = await service.activate("raw_code", client_id)

    assert result.last_activated_client_id == client_id
    assert result.is_active is True
    mock_uow.invite_codes.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_activate_code_not_found(service, mock_uow):
    mock_uow.invite_codes.get_by_code_hash.return_value = None

    with patch("app.application.services.invite_codes.SecurityUtils.hash_invite_code", return_value="missing"):
        with pytest.raises(InvalidInviteCodeError, match="not found"):
            await service.activate("raw", uuid4())


@pytest.mark.asyncio
async def test_activate_expired_code(service, mock_uow):
    from datetime import datetime, timedelta, timezone

    rp_id = uuid4()
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    invite = ClientInviteCode.create(
        retail_point_id=rp_id,
        encrypted_code="enc",
        code_hash="hash",
        created_by_employee_id=uuid4(),
        expires_in=timedelta(minutes=-30),
        now=past,
    )
    mock_uow.invite_codes.get_by_code_hash.return_value = invite

    with patch("app.application.services.invite_codes.SecurityUtils.hash_invite_code", return_value="hash"):
        with pytest.raises(InvalidInviteCodeError, match="invalid or expired"):
            await service.activate("raw", uuid4())


# --- deactivate ---

@pytest.mark.asyncio
async def test_deactivate_success(service, mock_uow):
    uid = uuid4()
    invite = ClientInviteCode(
        retail_point_id=uuid4(), encrypted_code="enc", code_hash="h", created_by_employee_id=uuid4(), id=uid,
    )
    mock_uow.invite_codes.get_by_id.return_value = invite

    result = await service.deactivate(uid)

    assert result.is_active is False
    mock_uow.invite_codes.update.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_deactivate_not_found(service, mock_uow):
    mock_uow.invite_codes.get_by_id.return_value = None

    with pytest.raises(InvalidInviteCodeError, match="not found"):
        await service.deactivate(uuid4())


# --- get ---

@pytest.mark.asyncio
async def test_get_success(service, mock_uow):
    uid = uuid4()
    invite = ClientInviteCode(
        retail_point_id=uuid4(), encrypted_code="enc", code_hash="h", created_by_employee_id=uuid4(), id=uid,
    )
    mock_uow.invite_codes.get_by_id.return_value = invite

    result = await service.get(uid)
    assert result.id == uid


@pytest.mark.asyncio
async def test_get_not_found(service, mock_uow):
    mock_uow.invite_codes.get_by_id.return_value = None

    with pytest.raises(InvalidInviteCodeError, match="not found"):
        await service.get(uuid4())


# --- get_by_retail_point ---

@pytest.mark.asyncio
async def test_get_by_retail_point_success(service, mock_uow):
    rp_id = uuid4()
    invite = ClientInviteCode(
        retail_point_id=rp_id, encrypted_code="enc", code_hash="h", created_by_employee_id=uuid4(),
    )
    mock_uow.invite_codes.get_by_retail_point.return_value = invite

    result = await service.get_by_retail_point(rp_id)
    assert result.retail_point_id == rp_id


@pytest.mark.asyncio
async def test_get_by_retail_point_not_found(service, mock_uow):
    mock_uow.invite_codes.get_by_retail_point.return_value = None

    with pytest.raises(InvalidInviteCodeError, match="not found"):
        await service.get_by_retail_point(uuid4())


# --- helpers ---


def _make_employee(**overrides):
    defaults = dict(phone="+998900000000", password_hash="h", full_name="Emp")
    defaults.update(overrides)
    return Employee(**defaults)
