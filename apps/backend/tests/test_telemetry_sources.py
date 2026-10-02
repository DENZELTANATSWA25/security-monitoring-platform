"""Tests for administrative telemetry source management."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.telemetry_source import TelemetrySource
from app.models.audit_log import AuditLog
from app.models.telemetry_source import TelemetrySource

from app.services.telemetry_source_service import create_telemetry_source


async def test_admin_can_create_telemetry_source(
    admin_client: AsyncClient,
) -> None:
    """Administrators should be able to register telemetry producers."""

    response = await admin_client.post(
        "/api/v1/telemetry-sources",
        json={
            "name": "Linux Production Agent",
            "source_type": "linux-agent",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Linux Production Agent"
    assert body["source_type"] == "linux-agent"
    assert body["is_active"] is True
    assert body["key_id"]
    assert body["credential"].startswith(
        f"smp_{body['key_id']}."
    )

    # Secret hashes must never be exposed through the API.
    assert "api_key_hash" not in body


async def test_analyst_cannot_create_telemetry_source(
    analyst_client: AsyncClient,
) -> None:
    """Analysts must not be allowed to provision machine credentials."""

    response = await analyst_client.post(
        "/api/v1/telemetry-sources",
        json={
            "name": "Unauthorized Analyst Source",
            "source_type": "test-agent",
        },
    )

    assert response.status_code == 403


async def test_viewer_cannot_create_telemetry_source(
    viewer_client: AsyncClient,
) -> None:
    """Viewers must not be allowed to provision machine credentials."""

    response = await viewer_client.post(
        "/api/v1/telemetry-sources",
        json={
            "name": "Unauthorized Viewer Source",
            "source_type": "test-agent",
        },
    )

    assert response.status_code == 403


async def test_unauthenticated_user_cannot_manage_telemetry_sources(
    client: AsyncClient,
) -> None:
    """Telemetry source management must require human authentication."""

    response = await client.get(
        "/api/v1/telemetry-sources",
    )

    assert response.status_code == 401


async def test_admin_can_list_telemetry_sources(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to inspect registered producers."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="List Test Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await admin_client.get(
        "/api/v1/telemetry-sources",
    )

    assert response.status_code == 200

    body = response.json()

    matching_sources = [
        item
        for item in body
        if item["id"] == source.id
    ]

    assert len(matching_sources) == 1

    returned_source = matching_sources[0]

    assert returned_source["name"] == "List Test Source"
    assert "api_key_hash" not in returned_source
    assert "credential" not in returned_source


async def test_admin_can_read_telemetry_source(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to inspect one producer."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Detail Test Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await admin_client.get(
        f"/api/v1/telemetry-sources/{source.id}",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == source.id
    assert body["name"] == "Detail Test Source"
    assert "api_key_hash" not in body
    assert "credential" not in body


async def test_unknown_telemetry_source_returns_404(
    admin_client: AsyncClient,
) -> None:
    """Requesting an unknown telemetry source should return not found."""

    response = await admin_client.get(
        "/api/v1/telemetry-sources/999999",
    )

    assert response.status_code == 404


async def test_duplicate_telemetry_source_name_returns_409(
    admin_client: AsyncClient,
) -> None:
    """Telemetry source names must remain unique."""

    payload = {
        "name": "Duplicate Source",
        "source_type": "test-agent",
    }

    first_response = await admin_client.post(
        "/api/v1/telemetry-sources",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = await admin_client.post(
        "/api/v1/telemetry-sources",
        json=payload,
    )

    assert second_response.status_code == 409


async def test_admin_can_revoke_telemetry_source(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to revoke producer credentials."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Revocation Test Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await admin_client.post(
        f"/api/v1/telemetry-sources/{source.id}/revoke",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == source.id
    assert body["is_active"] is False
    assert "api_key_hash" not in body
    assert "credential" not in body

    await db_session.refresh(source)

    assert source.is_active is False


async def test_analyst_cannot_revoke_telemetry_source(
    analyst_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Analysts must not be allowed to revoke producer credentials."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Analyst Revocation Test",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await analyst_client.post(
        f"/api/v1/telemetry-sources/{source.id}/revoke",
    )

    assert response.status_code == 403


async def test_revoking_unknown_source_returns_404(
    admin_client: AsyncClient,
) -> None:
    """Revoking an unknown telemetry source should return not found."""

    response = await admin_client.post(
        "/api/v1/telemetry-sources/999999/revoke",
    )

    assert response.status_code == 404


async def test_creating_telemetry_source_creates_audit_log(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Creating a telemetry source should leave an administrative audit record."""

    response = await admin_client.post(
        "/api/v1/telemetry-sources",
        json={
            "name": "Audited Linux Agent",
            "source_type": "linux-agent",
        },
    )

    assert response.status_code == 201

    source_id = response.json()["id"]

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "TELEMETRY_SOURCE_CREATED",
            AuditLog.resource == "TELEMETRY_SOURCE",
        )
    )

    audit_log = result.scalar_one()

    assert audit_log.user_id is not None
    assert f"id={source_id}" in audit_log.details
    assert "Audited Linux Agent" in audit_log.details


async def test_revoking_telemetry_source_creates_audit_log(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Revoking a telemetry source should leave an administrative audit record."""

    create_response = await admin_client.post(
        "/api/v1/telemetry-sources",
        json={
            "name": "Revocation Audit Agent",
            "source_type": "linux-agent",
        },
    )

    assert create_response.status_code == 201

    source_id = create_response.json()["id"]

    revoke_response = await admin_client.post(
        f"/api/v1/telemetry-sources/{source_id}/revoke",
    )

    assert revoke_response.status_code == 200

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action == "TELEMETRY_SOURCE_REVOKED",
            AuditLog.resource == "TELEMETRY_SOURCE",
        )
    )

    audit_log = result.scalar_one()

    assert audit_log.user_id is not None
    assert f"id={source_id}" in audit_log.details
    assert "Revocation Audit Agent" in audit_log.details

async def test_telemetry_source_creation_rolls_back_when_audit_fails(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """
    Telemetry source creation and its audit record must be atomic.

    If audit logging fails, the newly created source must not persist.
    """

    async def failing_log_event(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        "app.api.v1.endpoints.telemetry_sources.log_event",
        failing_log_event,
    )

    try:
        await admin_client.post(
            "/api/v1/telemetry-sources",
            json={
                "name": "Atomicity Test Agent",
                "source_type": "linux-agent",
            },
        )
    except RuntimeError as exc:
        assert str(exc) == "Simulated audit failure"

    # The session may be left inside the failed request transaction.
    # Explicitly roll it back before checking database state.
    await db_session.rollback()

    result = await db_session.execute(
        select(TelemetrySource).where(
            TelemetrySource.name == "Atomicity Test Agent",
        )
    )

    source = result.scalar_one_or_none()

    assert source is None

async def test_telemetry_source_revocation_rolls_back_when_audit_fails(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """
    Telemetry source revocation and its audit record must be atomic.

    If audit logging fails, the source must remain active.
    """

    # Create the source normally first.
    create_response = await admin_client.post(
        "/api/v1/telemetry-sources",
        json={
            "name": "Revocation Atomicity Agent",
            "source_type": "linux-agent",
        },
    )

    assert create_response.status_code == 201

    source_id = create_response.json()["id"]

    async def failing_log_event(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        "app.api.v1.endpoints.telemetry_sources.log_event",
        failing_log_event,
    )

    try:
        await admin_client.post(
            f"/api/v1/telemetry-sources/{source_id}/revoke",
        )
    except RuntimeError as exc:
        assert str(exc) == "Simulated audit failure"

    await db_session.rollback()

    result = await db_session.execute(
        select(TelemetrySource).where(
            TelemetrySource.id == source_id,
        )
    )

    source = result.scalar_one()

    assert source.is_active is True