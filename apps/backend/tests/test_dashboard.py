"""Tests for dashboard security metrics."""

from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.login_attempt import LoginAttempt
from app.models.security_event import EventSeverity, SecurityEvent


async def test_unauthenticated_user_cannot_read_dashboard(
    client: AsyncClient,
) -> None:
    """Dashboard metrics require authentication."""

    response = await client.get(
        "/api/v1/dashboard/summary",
    )

    assert response.status_code == 401


async def test_authenticated_viewer_can_read_dashboard(
    viewer_client: AsyncClient,
) -> None:
    """Authenticated viewers should have read access to dashboard metrics."""

    response = await viewer_client.get(
        "/api/v1/dashboard/summary",
    )

    assert response.status_code == 200


async def test_empty_dashboard_returns_zero_metrics(
    viewer_client: AsyncClient,
) -> None:
    """An empty security dataset should produce zero-valued metrics."""

    response = await viewer_client.get(
        "/api/v1/dashboard/summary",
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_events": 0,
        "critical_events": 0,
        "active_alerts": 0,
        "resolved_alerts": 0,
        "failed_logins_24h": 0,
        "successful_logins_24h": 1,
    }


async def test_dashboard_returns_security_metrics(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Dashboard metrics should reflect persisted security data."""

    now = datetime.utcnow()

    db_session.add_all(
        [
            SecurityEvent(
                event_type="DASHBOARD_CRITICAL",
                severity=EventSeverity.CRITICAL,
                source="pytest",
                message="Critical dashboard event.",
            ),
            SecurityEvent(
                event_type="DASHBOARD_INFO",
                severity=EventSeverity.INFO,
                source="pytest",
                message="Informational dashboard event.",
            ),
            Alert(
                alert_type="DASHBOARD_ACTIVE",
                severity="HIGH",
                message="Active dashboard alert.",
                resolved=False,
            ),
            Alert(
                alert_type="DASHBOARD_RESOLVED",
                severity="MEDIUM",
                message="Resolved dashboard alert.",
                resolved=True,
            ),
            LoginAttempt(
                email="failed-recent@example.com",
                successful=False,
                ip_address="192.0.2.10",
                timestamp=now - timedelta(hours=1),
            ),
            LoginAttempt(
                email="successful-recent@example.com",
                successful=True,
                ip_address="192.0.2.11",
                timestamp=now - timedelta(hours=2),
            ),
            LoginAttempt(
                email="failed-old@example.com",
                successful=False,
                ip_address="192.0.2.12",
                timestamp=now - timedelta(hours=25),
            ),
        ]
    )

    await db_session.flush()

    response = await viewer_client.get(
        "/api/v1/dashboard/summary",
    )

    assert response.status_code == 200
    assert response.json() == {
        "total_events": 2,
        "critical_events": 1,
        "active_alerts": 1,
        "resolved_alerts": 1,
        "failed_logins_24h": 1,
        "successful_logins_24h": 2,
    }
