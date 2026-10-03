"""Tests for administrative telemetry source management."""

from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.telemetry_source import TelemetrySource
from app.models.audit_log import AuditLog

from app.models.security_event import SecurityEvent, EventSeverity

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

async def test_telemetry_source_status_requires_authentication(
    client: AsyncClient,
) -> None:
    """Operational telemetry status must not be publicly accessible."""

    response = await client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 401


async def test_viewer_cannot_read_telemetry_source_status(
    viewer_client: AsyncClient,
) -> None:
    """Viewers must not have access to telemetry source monitoring."""

    response = await viewer_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 403


async def test_analyst_can_read_telemetry_source_status(
    analyst_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Analysts should be able to monitor telemetry producers."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Analyst Status Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await analyst_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 200

    matching_sources = [
        item
        for item in response.json()
        if item["id"] == source.id
    ]

    assert len(matching_sources) == 1


async def test_never_connected_source_reports_never_connected(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A source with no successful ingestion should report NEVER_CONNECTED."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Never Connected Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await admin_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 200

    item = next(
        item
        for item in response.json()
        if item["id"] == source.id
    )

    assert item["health_status"] == "NEVER_CONNECTED"
    assert item["last_seen_at"] is None
    assert item["events_24h"] == 0
    assert item["last_event_at"] is None


async def test_recently_seen_source_reports_online(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A recently active source should report ONLINE."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Online Status Source",
        source_type="test-agent",
    )

    source.last_seen_at = datetime.utcnow()

    await db_session.commit()

    response = await admin_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 200

    item = next(
        item
        for item in response.json()
        if item["id"] == source.id
    )

    assert item["health_status"] == "ONLINE"


async def test_stale_source_reports_offline(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """An active source not seen recently should report OFFLINE."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Offline Status Source",
        source_type="test-agent",
    )

    source.last_seen_at = (
        datetime.utcnow()
        - timedelta(minutes=10)
    )

    await db_session.commit()

    response = await admin_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 200

    item = next(
        item
        for item in response.json()
        if item["id"] == source.id
    )

    assert item["health_status"] == "OFFLINE"


async def test_revoked_source_reports_revoked(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Revocation should take precedence over activity state."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Revoked Status Source",
        source_type="test-agent",
    )

    source.last_seen_at = datetime.utcnow()
    source.is_active = False

    await db_session.commit()

    response = await admin_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 200

    item = next(
        item
        for item in response.json()
        if item["id"] == source.id
    )

    assert item["health_status"] == "REVOKED"

async def test_telemetry_source_status_reports_event_statistics(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    Status should count only events from the last 24 hours while
    preserving the most recent event timestamp across all history.
    """

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Statistics Test Source",
        source_type="test-agent",
    )

    other_source, _ = await create_telemetry_source(
        db=db_session,
        name="Unrelated Statistics Source",
        source_type="test-agent",
    )

    now = datetime.utcnow()

    old_event = SecurityEvent(
        event_type="OLD_TELEMETRY_EVENT",
        severity=EventSeverity.INFO,
        source="statistics-test",
        message="Historical event",
        telemetry_source_id=source.id,
        created_at=now - timedelta(days=3),
    )

    recent_event_one = SecurityEvent(
        event_type="RECENT_TELEMETRY_EVENT_ONE",
        severity=EventSeverity.INFO,
        source="statistics-test",
        message="Recent event one",
        telemetry_source_id=source.id,
        created_at=now - timedelta(hours=2),
    )

    recent_event_two = SecurityEvent(
        event_type="RECENT_TELEMETRY_EVENT_TWO",
        severity=EventSeverity.WARNING,
        source="statistics-test",
        message="Recent event two",
        telemetry_source_id=source.id,
        created_at=now - timedelta(minutes=30),
    )

    unrelated_event = SecurityEvent(
        event_type="UNRELATED_TELEMETRY_EVENT",
        severity=EventSeverity.INFO,
        source="unrelated-test",
        message="Event belonging to another producer",
        telemetry_source_id=other_source.id,
        created_at=now - timedelta(minutes=5),
    )

    db_session.add_all(
        [
            old_event,
            recent_event_one,
            recent_event_two,
            unrelated_event,
        ]
    )

    await db_session.commit()

    response = await admin_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 200

    item = next(
        item
        for item in response.json()
        if item["id"] == source.id
    )

    assert item["events_24h"] == 2
    assert item["last_event_at"] is not None

    returned_last_event = datetime.fromisoformat(
        item["last_event_at"],
    )

    assert returned_last_event == recent_event_two.created_at

async def test_old_event_is_preserved_as_last_event(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    A historical event should not count toward events_24h but should
    still be reported as the source's most recent known event.
    """

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Historical Event Source",
        source_type="test-agent",
    )

    event = SecurityEvent(
        event_type="HISTORICAL_TELEMETRY_EVENT",
        severity=EventSeverity.INFO,
        source="historical-test",
        message="Historical telemetry",
        telemetry_source_id=source.id,
        created_at=datetime.utcnow() - timedelta(days=3),
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    response = await admin_client.get(
        "/api/v1/telemetry-sources/status",
    )

    assert response.status_code == 200

    item = next(
        item
        for item in response.json()
        if item["id"] == source.id
    )

    assert item["events_24h"] == 0
    assert item["last_event_at"] is not None

    assert datetime.fromisoformat(
        item["last_event_at"],
    ) == event.created_at


async def test_admin_can_rotate_telemetry_source_credential(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to rotate producer credentials."""

    source, old_credential = await create_telemetry_source(
        db=db_session,
        name="Rotation Endpoint Source",
        source_type="test-agent",
    )

    await db_session.commit()

    old_key_id = source.key_id

    response = await admin_client.post(
        f"/api/v1/telemetry-sources/{source.id}/rotate-credential",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == source.id
    assert body["key_id"] != old_key_id
    assert body["credential"].startswith(
        f"smp_{body['key_id']}."
    )

    assert "api_key_hash" not in body
    assert old_credential.credential != body["credential"]


async def test_analyst_cannot_rotate_telemetry_source_credential(
    analyst_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Analysts must not be allowed to rotate producer credentials."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Analyst Rotation Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await analyst_client.post(
        f"/api/v1/telemetry-sources/{source.id}/rotate-credential",
    )

    assert response.status_code == 403


async def test_viewer_cannot_rotate_telemetry_source_credential(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Viewers must not be allowed to rotate producer credentials."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Viewer Rotation Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await viewer_client.post(
        f"/api/v1/telemetry-sources/{source.id}/rotate-credential",
    )

    assert response.status_code == 403


async def test_rotating_unknown_telemetry_source_returns_404(
    admin_client: AsyncClient,
) -> None:
    """Rotating an unknown source should return not found."""

    response = await admin_client.post(
        "/api/v1/telemetry-sources/999999/rotate-credential",
    )

    assert response.status_code == 404


async def test_revoked_telemetry_source_credential_cannot_be_rotated(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Credential rotation must not reactivate revoked telemetry sources."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Revoked Rotation Source",
        source_type="test-agent",
    )

    source.is_active = False

    await db_session.commit()

    response = await admin_client.post(
        f"/api/v1/telemetry-sources/{source.id}/rotate-credential",
    )

    assert response.status_code == 409


async def test_rotated_credential_invalidates_old_ingestion_credential(
    admin_client: AsyncClient,
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    After rotation, the old producer credential must fail while the
    replacement credential authenticates successfully.
    """

    source, old_credential = await create_telemetry_source(
        db=db_session,
        name="Ingestion Rotation Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await admin_client.post(
        f"/api/v1/telemetry-sources/{source.id}/rotate-credential",
    )

    assert response.status_code == 200

    new_credential = response.json()["credential"]

    event = {
        "event_type": "ROTATION_TEST_EVENT",
        "severity": "WARNING",
        "source": "rotation-test-agent",
        "description": "Credential rotation integration test",
    }

    old_response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": old_credential.credential,
        },
        json=event,
    )

    assert old_response.status_code == 401

    new_response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": new_credential,
        },
        json=event,
    )

    assert new_response.status_code == 201


async def test_rotating_telemetry_source_credential_creates_audit_log(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Credential rotation should leave an administrative audit record."""

    source, _ = await create_telemetry_source(
        db=db_session,
        name="Rotation Audit Source",
        source_type="test-agent",
    )

    await db_session.commit()

    response = await admin_client.post(
        f"/api/v1/telemetry-sources/{source.id}/rotate-credential",
    )

    assert response.status_code == 200

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action
            == "TELEMETRY_SOURCE_CREDENTIAL_ROTATED",
            AuditLog.resource == "TELEMETRY_SOURCE",
        )
    )

    audit_log = result.scalar_one()

    assert audit_log.user_id is not None
    assert f"id={source.id}" in audit_log.details
    assert "Rotation Audit Source" in audit_log.details

    # Credential material must never appear in audit records.
    assert response.json()["credential"] not in audit_log.details


async def test_credential_rotation_rolls_back_when_audit_fails(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """
    Credential rotation and its audit record must be atomic.

    If audit logging fails, the original credential must remain valid.
    """

    source, original_credential = await create_telemetry_source(
        db=db_session,
        name="Rotation Atomicity Source",
        source_type="test-agent",
    )

    await db_session.commit()

    source_id = source.id
    original_key_id = source.key_id
    original_hash = source.api_key_hash

    async def failing_log_event(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        "app.api.v1.endpoints.telemetry_sources.log_event",
        failing_log_event,
    )

    try:
        await admin_client.post(
            f"/api/v1/telemetry-sources/{source.id}/rotate-credential",
        )
    except RuntimeError as exc:
        assert str(exc) == "Simulated audit failure"

    await db_session.rollback()

    result = await db_session.execute(
        select(TelemetrySource).where(
            TelemetrySource.id == source_id,
        )
    )

    stored_source = result.scalar_one()

    assert stored_source.key_id == original_key_id
    assert stored_source.api_key_hash == original_hash

    # The original credential must still authenticate after rollback.
    from app.services.telemetry_source_service import (
        authenticate_telemetry_source,
    )

    authenticated_source = await authenticate_telemetry_source(
        db=db_session,
        credential=original_credential.credential,
    )

    assert authenticated_source is not None
    assert authenticated_source.id == stored_source.id