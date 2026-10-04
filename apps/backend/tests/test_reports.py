"""Tests for security reporting endpoints."""

from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.login_attempt import LoginAttempt
from app.models.security_event import EventSeverity, SecurityEvent


async def test_unauthenticated_user_cannot_read_security_report(
    client: AsyncClient,
) -> None:
    """Security reports require authentication."""

    response = await client.get(
        "/api/v1/reports/security-summary",
    )

    assert response.status_code == 401


async def test_authenticated_viewer_can_read_security_report(
    viewer_client: AsyncClient,
) -> None:
    """Authenticated viewers should have read access to security reports."""

    response = await viewer_client.get(
        "/api/v1/reports/security-summary",
    )

    assert response.status_code == 200


async def test_empty_security_report_returns_zero_metrics(
    viewer_client: AsyncClient,
) -> None:
    """An empty database should produce an empty security summary."""

    response = await viewer_client.get(
        "/api/v1/reports/security-summary",
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_events": 0,
        "critical_events": 0,
        "active_alerts": 0,
        "resolved_alerts": 0,
        "failed_logins_24h": 0,
        "successful_logins_24h": 1,
        "severity_distribution": [],
        "event_type_distribution": [],
        "alert_severity_distribution": [],
    }


async def test_security_report_returns_aggregated_metrics(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Security reports should aggregate persisted operational data."""

    now = datetime.utcnow()

    db_session.add_all(
        [
            SecurityEvent(
                event_type="REPORT_LOGIN",
                severity=EventSeverity.CRITICAL,
                source="pytest",
                message="Critical report event.",
            ),
            SecurityEvent(
                event_type="REPORT_LOGIN",
                severity=EventSeverity.INFO,
                source="pytest",
                message="Informational report event.",
            ),
            Alert(
                alert_type="REPORT_ACTIVE",
                severity="HIGH",
                message="Active report alert.",
                resolved=False,
            ),
            Alert(
                alert_type="REPORT_RESOLVED",
                severity="MEDIUM",
                message="Resolved report alert.",
                resolved=True,
            ),
            LoginAttempt(
                email="report-failed@example.com",
                successful=False,
                ip_address="192.0.2.20",
                timestamp=now - timedelta(hours=1),
            ),
            LoginAttempt(
                email="report-success@example.com",
                successful=True,
                ip_address="192.0.2.21",
                timestamp=now - timedelta(hours=2),
            ),
            LoginAttempt(
                email="report-old@example.com",
                successful=False,
                ip_address="192.0.2.22",
                timestamp=now - timedelta(hours=25),
            ),
        ]
    )

    await db_session.flush()

    response = await viewer_client.get(
        "/api/v1/reports/security-summary",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_events"] == 2
    assert body["critical_events"] == 1
    assert body["active_alerts"] == 1
    assert body["resolved_alerts"] == 1
    assert body["failed_logins_24h"] == 1
    assert body["successful_logins_24h"] == 2

    assert {
        item["name"]: item["count"]
        for item in body["severity_distribution"]
    } == {
        "CRITICAL": 1,
        "INFO": 1,
    }

    assert {
        item["name"]: item["count"]
        for item in body["event_type_distribution"]
    } == {
        "REPORT_LOGIN": 2,
    }

    assert {
        item["name"]: item["count"]
        for item in body["alert_severity_distribution"]
    } == {
        "HIGH": 1,
        "MEDIUM": 1,
    }
