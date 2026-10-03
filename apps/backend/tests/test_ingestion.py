"""Tests for authenticated external telemetry ingestion."""

from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent
from app.services.telemetry_source_service import create_telemetry_source
from app.models.alert import Alert


async def test_ingestion_requires_credentials(
    client: AsyncClient,
) -> None:
    """External telemetry must not be accepted anonymously."""

    response = await client.post(
        "/api/v1/ingestion/events",
        json={
            "event_type": "SSH_LOGIN_FAILURE",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "Failed SSH login",
        },
    )

    assert response.status_code == 401


async def test_ingestion_rejects_invalid_credentials(
    client: AsyncClient,
) -> None:
    """Malformed telemetry credentials must be rejected."""

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": "incorrect-key",
        },
        json={
            "event_type": "SSH_LOGIN_FAILURE",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "Failed SSH login",
        },
    )

    assert response.status_code == 401


async def test_ingestion_rejects_revoked_source(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A revoked telemetry source must not be allowed to ingest events."""

    source, credential = await create_telemetry_source(
        db=db_session,
        name="Revoked Ingestion Source",
        source_type="test-agent",
    )

    source.is_active = False
    await db_session.flush()

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": credential.credential,
        },
        json={
            "event_type": "SSH_LOGIN_FAILURE",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "Failed SSH login",
        },
    )

    assert response.status_code == 401


async def test_authenticated_external_event_is_ingested(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """A registered telemetry source should enter the event pipeline."""

    source, credential = await create_telemetry_source(
        db=db_session,
        name="Linux Test Agent",
        source_type="linux-agent",
    )

    occurred_at = "2026-10-01T18:30:00"

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": credential.credential,
        },
        json={
            "event_type": "SSH_LOGIN_FAILURE",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "Failed password for root",
            "occurred_at": occurred_at,
            "event_metadata": {
                "source_ip": "203.0.113.50",
                "hostname": "linux-server-01",
            },
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["event_type"] == "SSH_LOGIN_FAILURE"
    assert body["source"] == "linux-server-01"
    assert body["user_id"] is None

    result = await db_session.execute(
        select(SecurityEvent).where(
            SecurityEvent.id == body["id"],
        )
    )

    event = result.scalar_one()

    assert event.occurred_at == datetime(
        2026,
        10,
        1,
        18,
        30,
    )

    assert event.event_metadata == {
        "source_ip": "203.0.113.50",
        "hostname": "linux-server-01",
    }

    await db_session.refresh(source)

    assert source.last_seen_at is not None


async def test_external_ingestion_runs_detection_and_creates_alert(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    Authenticated external telemetry must pass through the canonical
    detection pipeline and persist any generated alerts.
    """

    source, credential = await create_telemetry_source(
        db=db_session,
        name="Burst Detection Test Agent",
        source_type="test-agent",
    )

    event_source = "external-burst-test-source"

    # The existing EVENT_BURST rule triggers when five recent events
    # originate from the same source.
    for index in range(5):
        response = await client.post(
            "/api/v1/ingestion/events",
            headers={
                "X-Ingestion-Key": credential.credential,
            },
            json={
                "event_type": f"EXTERNAL_BURST_EVENT_{index}",
                "severity": "WARNING",
                "source": event_source,
                "description": f"External burst event {index}",
                "event_metadata": {
                    "hostname": event_source,
                },
            },
        )

        assert response.status_code == 201

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "EVENT_BURST",
        )
    )

    alerts = result.scalars().all()

    assert len(alerts) == 1

    alert = alerts[0]

    assert alert.severity == "HIGH"
    assert alert.message is not None
    assert event_source in alert.message


async def test_ingestion_rejects_blank_required_text(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Required telemetry text must contain meaningful content."""

    _, credential = await create_telemetry_source(
        db=db_session,
        name="Blank Validation Test Agent",
        source_type="test-agent",
    )

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": credential.credential,
        },
        json={
            "event_type": "   ",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "Test event",
        },
    )

    assert response.status_code == 422


async def test_ingestion_rejects_oversized_description(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Telemetry descriptions must respect the ingestion size boundary."""

    _, credential = await create_telemetry_source(
        db=db_session,
        name="Description Validation Test Agent",
        source_type="test-agent",
    )

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": credential.credential,
        },
        json={
            "event_type": "OVERSIZED_DESCRIPTION",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "x" * 10_001,
        },
    )

    assert response.status_code == 422


async def test_ingestion_rejects_event_too_far_in_future(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Telemetry timestamps implausibly far in the future must be rejected."""

    _, credential = await create_telemetry_source(
        db=db_session,
        name="Timestamp Validation Test Agent",
        source_type="test-agent",
    )

    future_time = datetime.utcnow() + timedelta(
        minutes=10,
    )

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": credential.credential,
        },
        json={
            "event_type": "FUTURE_EVENT",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "Event with invalid future timestamp.",
            "occurred_at": future_time.isoformat(),
        },
    )

    assert response.status_code == 422