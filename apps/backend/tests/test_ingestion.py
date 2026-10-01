"""Tests for authenticated external telemetry ingestion."""

from datetime import datetime

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.security_event import SecurityEvent


TEST_INGESTION_KEY = "test-ingestion-key"


async def test_ingestion_requires_credentials(
    client: AsyncClient,
    monkeypatch,
) -> None:
    """External telemetry must not be accepted anonymously."""

    monkeypatch.setattr(
        settings,
        "INGESTION_API_KEY",
        TEST_INGESTION_KEY,
    )

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
    monkeypatch,
) -> None:
    """An incorrect ingestion key must be rejected."""

    monkeypatch.setattr(
        settings,
        "INGESTION_API_KEY",
        TEST_INGESTION_KEY,
    )

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


async def test_ingestion_fails_closed_when_not_configured(
    client: AsyncClient,
    monkeypatch,
) -> None:
    """An unset server key must disable external ingestion."""

    monkeypatch.setattr(
        settings,
        "INGESTION_API_KEY",
        "",
    )

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": TEST_INGESTION_KEY,
        },
        json={
            "event_type": "SSH_LOGIN_FAILURE",
            "severity": "WARNING",
            "source": "linux-server-01",
            "description": "Failed SSH login",
        },
    )

    assert response.status_code == 503


async def test_authenticated_external_event_is_ingested(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Authenticated external telemetry should enter the event pipeline."""

    monkeypatch.setattr(
        settings,
        "INGESTION_API_KEY",
        TEST_INGESTION_KEY,
    )

    occurred_at = "2026-10-01T18:30:00"

    response = await client.post(
        "/api/v1/ingestion/events",
        headers={
            "X-Ingestion-Key": TEST_INGESTION_KEY,
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