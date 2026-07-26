from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.domain.entities.visits import Visit
from app.domain.entities.auth import AuthenticatedEmployee
from app.domain.entities.visit_media import VisitMedia
from app.domain.entities.visit_debts import VisitDebt
from app.domain.enums import VisitStatus
from app.infrastructure.postgres.models.enums import EmployeeRole
from app.api.dependencies import get_visits_service, get_visit_media_service, get_current_user


@pytest.fixture
def mock_visits_service():
    return AsyncMock()


@pytest.fixture
def mock_visit_media_service():
    return AsyncMock()


@pytest.fixture
def mock_admin_employee():
    return AuthenticatedEmployee(
        id=uuid4(),
        phone="+998900000000",
        role=EmployeeRole.ADMIN,
        full_name="Mock Admin",
        is_active=True,
    )


@pytest.fixture(autouse=True)
def override_deps(mock_visits_service, mock_visit_media_service, mock_admin_employee):
    app.dependency_overrides[get_visits_service] = lambda: mock_visits_service
    app.dependency_overrides[get_visit_media_service] = lambda: mock_visit_media_service
    app.dependency_overrides[get_current_user] = lambda: mock_admin_employee
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def _visit_response(status=VisitStatus.IN_PROGRESS):
    return Visit(
        id=uuid4(),
        employee_id=uuid4(),
        retail_point_id=uuid4(),
        status=status,
        started_at=datetime.now(UTC),
    )


def _visit_media_response():
    return VisitMedia(
        id=uuid4(),
        visit_id=uuid4(),
        media_id=uuid4(),
        created_at=datetime.now(UTC),
    )


def _visit_debt_response():
    return VisitDebt(
        id=uuid4(),
        visit_id=uuid4(),
        amount=Decimal("50000.00"),
        comment="Test debt",
        created_at=datetime.now(UTC),
    )


# ======================================================================
# 1. BASE VISIT OPERATIONS
# ======================================================================

# --- POST /api/v1/visits/start ---

@pytest.mark.asyncio
async def test_start_visit_success(client, mock_visits_service):
    visit = _visit_response()
    mock_visits_service.start_visit.return_value = visit

    resp = await client.post(
        "/api/v1/visits/start",
        params={"retail_point_id": str(uuid4())},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == VisitStatus.IN_PROGRESS.value


@pytest.mark.asyncio
async def test_start_visit_already_active(client, mock_visits_service):
    from app.core.extensions import EmployeeHasActiveVisitError
    mock_visits_service.start_visit.side_effect = EmployeeHasActiveVisitError()

    resp = await client.post(
        "/api/v1/visits/start",
        params={"retail_point_id": str(uuid4())},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_start_visit_retail_point_not_found(client, mock_visits_service):
    from app.core.extensions import RetailPointNotFoundError
    mock_visits_service.start_visit.side_effect = RetailPointNotFoundError()

    resp = await client.post(
        "/api/v1/visits/start",
        params={"retail_point_id": str(uuid4())},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_start_visit_retail_point_inactive(client, mock_visits_service):
    from app.core.extensions import RetailPointInactiveError
    mock_visits_service.start_visit.side_effect = RetailPointInactiveError()

    resp = await client.post(
        "/api/v1/visits/start",
        params={"retail_point_id": str(uuid4())},
    )
    assert resp.status_code == 409


# --- POST /api/v1/visits/{visit_id}/finish ---

@pytest.mark.asyncio
async def test_finish_visit_success(client, mock_visits_service):
    visit = _visit_response(status=VisitStatus.COMPLETED)
    mock_visits_service.finish_visit.return_value = visit

    resp = await client.post(f"/api/v1/visits/{uuid4()}/finish")
    assert resp.status_code == 200
    assert resp.json()["status"] == VisitStatus.COMPLETED.value


@pytest.mark.asyncio
async def test_finish_visit_not_found(client, mock_visits_service):
    from app.core.extensions import VisitNotFoundError
    mock_visits_service.finish_visit.side_effect = VisitNotFoundError()

    resp = await client.post(f"/api/v1/visits/{uuid4()}/finish")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_finish_visit_already_finished(client, mock_visits_service):
    mock_visits_service.finish_visit.side_effect = ValueError("already finished")

    resp = await client.post(f"/api/v1/visits/{uuid4()}/finish")
    assert resp.status_code == 400


# --- POST /api/v1/visits/{visit_id}/cancel ---

@pytest.mark.asyncio
async def test_cancel_visit_success(client, mock_visits_service):
    visit = _visit_response(status=VisitStatus.CANCELLED)
    mock_visits_service.cancel_visit.return_value = visit

    resp = await client.post(f"/api/v1/visits/{uuid4()}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == VisitStatus.CANCELLED.value


@pytest.mark.asyncio
async def test_cancel_visit_not_found(client, mock_visits_service):
    from app.core.extensions import VisitNotFoundError
    mock_visits_service.cancel_visit.side_effect = VisitNotFoundError()

    resp = await client.post(f"/api/v1/visits/{uuid4()}/cancel")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_visit_already_cancelled(client, mock_visits_service):
    mock_visits_service.cancel_visit.side_effect = ValueError("already cancelled")

    resp = await client.post(f"/api/v1/visits/{uuid4()}/cancel")
    assert resp.status_code == 400


# --- GET /api/v1/visits/{visit_id} ---

@pytest.mark.asyncio
async def test_get_visit_success(client, mock_visits_service):
    visit = _visit_response()
    mock_visits_service.get_visit.return_value = visit

    resp = await client.get(f"/api/v1/visits/{visit.id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == VisitStatus.IN_PROGRESS.value


@pytest.mark.asyncio
async def test_get_visit_not_found(client, mock_visits_service):
    from app.core.extensions import VisitNotFoundError
    mock_visits_service.get_visit.side_effect = VisitNotFoundError()

    resp = await client.get(f"/api/v1/visits/{uuid4()}")
    assert resp.status_code == 404


# --- GET /api/v1/visits ---

@pytest.mark.asyncio
async def test_list_visits(client, mock_visits_service):
    visits = [_visit_response(), _visit_response()]
    mock_visits_service.list.return_value = visits

    resp = await client.get("/api/v1/visits")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_list_visits_with_filters(client, mock_visits_service):
    mock_visits_service.list.return_value = []

    resp = await client.get(
        "/api/v1/visits",
        params={
            "employee_id": str(uuid4()),
            "retail_point_id": str(uuid4()),
            "status": "in_progress",
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0


# ======================================================================
# 2. VISIT MEDIA
# ======================================================================

# --- POST /api/v1/visits/{visit_id}/media ---

@pytest.mark.asyncio
async def test_attach_media_success(client, mock_visit_media_service):
    media = _visit_media_response()
    mock_visit_media_service.attach.return_value = media

    resp = await client.post(
        f"/api/v1/visits/{media.visit_id}/media",
        json={"media_id": str(media.media_id)},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["visit_id"] == str(media.visit_id)
    assert data["media_id"] == str(media.media_id)


@pytest.mark.asyncio
async def test_attach_media_visit_not_found(client, mock_visit_media_service):
    from app.core.extensions import VisitNotFoundError
    mock_visit_media_service.attach.side_effect = VisitNotFoundError()

    resp = await client.post(
        f"/api/v1/visits/{uuid4()}/media",
        json={"media_id": str(uuid4())},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_attach_media_already_attached(client, mock_visit_media_service):
    from app.core.extensions import VisitMediaAlreadyAttachedError
    mock_visit_media_service.attach.side_effect = VisitMediaAlreadyAttachedError()

    resp = await client.post(
        f"/api/v1/visits/{uuid4()}/media",
        json={"media_id": str(uuid4())},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_attach_media_not_active(client, mock_visit_media_service):
    from app.core.extensions import VisitNotActiveError
    mock_visit_media_service.attach.side_effect = VisitNotActiveError()

    resp = await client.post(
        f"/api/v1/visits/{uuid4()}/media",
        json={"media_id": str(uuid4())},
    )
    assert resp.status_code == 409


# --- DELETE /api/v1/visits/{visit_id}/media/{media_id} ---

@pytest.mark.asyncio
async def test_detach_media_success(client, mock_visit_media_service):
    mock_visit_media_service.detach.return_value = None

    resp = await client.delete(f"/api/v1/visits/{uuid4()}/media/{uuid4()}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_detach_media_not_found(client, mock_visit_media_service):
    from app.core.extensions import VisitMediaNotFoundError
    mock_visit_media_service.detach.side_effect = VisitMediaNotFoundError()

    resp = await client.delete(f"/api/v1/visits/{uuid4()}/media/{uuid4()}")
    assert resp.status_code == 404


# --- GET /api/v1/visits/{visit_id}/media ---

@pytest.mark.asyncio
async def test_list_visit_media(client, mock_visit_media_service):
    media_list = [_visit_media_response(), _visit_media_response()]
    mock_visit_media_service.list_media.return_value = media_list

    resp = await client.get(f"/api/v1/visits/{uuid4()}/media")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ======================================================================
# 3. VISIT DEBTS
# ======================================================================

# --- POST /api/v1/visits/{visit_id}/debts ---

@pytest.mark.asyncio
async def test_add_debt_success(client, mock_visits_service):
    debt = _visit_debt_response()
    mock_visits_service.add_debt.return_value = debt

    resp = await client.post(
        f"/api/v1/visits/{debt.visit_id}/debts",
        json={"amount": "50000.00", "comment": "Test debt"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == "50000.00"
    assert data["comment"] == "Test debt"


@pytest.mark.asyncio
async def test_add_debt_visit_not_found(client, mock_visits_service):
    from app.core.extensions import VisitNotFoundError
    mock_visits_service.add_debt.side_effect = VisitNotFoundError()

    resp = await client.post(
        f"/api/v1/visits/{uuid4()}/debts",
        json={"amount": "50000.00", "comment": "Test"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_debt_visit_not_active(client, mock_visits_service):
    from app.core.extensions import VisitNotActiveError
    mock_visits_service.add_debt.side_effect = VisitNotActiveError()

    resp = await client.post(
        f"/api/v1/visits/{uuid4()}/debts",
        json={"amount": "50000.00", "comment": "Test"},
    )
    assert resp.status_code == 409


# --- PATCH /api/v1/visits/debts/{debt_id} ---

@pytest.mark.asyncio
async def test_update_debt_success(client, mock_visits_service):
    debt = _visit_debt_response()
    mock_visits_service.update_debt.return_value = debt

    resp = await client.patch(
        f"/api/v1/visits/debts/{debt.id}",
        json={"amount": "75000.00", "comment": "Updated"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["amount"] == "50000.00"
    assert data["comment"] == "Test debt"


@pytest.mark.asyncio
async def test_update_debt_not_found(client, mock_visits_service):
    from app.core.extensions import VisitDebtNotFoundError
    mock_visits_service.update_debt.side_effect = VisitDebtNotFoundError()

    resp = await client.patch(
        f"/api/v1/visits/debts/{uuid4()}",
        json={"amount": "75000.00", "comment": "X"},
    )
    assert resp.status_code == 404


# --- DELETE /api/v1/visits/debts/{debt_id} ---

@pytest.mark.asyncio
async def test_delete_debt_success(client, mock_visits_service):
    mock_visits_service.delete_debt.return_value = None

    resp = await client.delete(f"/api/v1/visits/debts/{uuid4()}")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_debt_not_found(client, mock_visits_service):
    from app.core.extensions import VisitDebtNotFoundError
    mock_visits_service.delete_debt.side_effect = VisitDebtNotFoundError()

    resp = await client.delete(f"/api/v1/visits/debts/{uuid4()}")
    assert resp.status_code == 404
