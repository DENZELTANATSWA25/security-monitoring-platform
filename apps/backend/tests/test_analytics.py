"""Tests for security analytics endpoints."""

from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventSeverity, SecurityEvent


async def test_unauthenticated_user_cannot_read_event_analytics(
    client: AsyncClient,
) -> None:
    """Event analytics require authentication."""

    response = await client.get(
        "/api/v1/analytics/events",
    )

    assert response.status_code == 401


async def test_authenticated_viewer_can_read_event_analytics(
    viewer_client: AsyncClient,
) -> None:
    """Authenticated viewers should have read access to event analytics."""

    response = await viewer_client.get(
        "/api/v1/analytics/events",
    )

    assert response.status_code == 200


async def test_empty_event_analytics_returns_empty_list(
    viewer_client: AsyncClient,
) -> None:
    """An empty event dataset should produce no trend entries."""

    response = await viewer_client.get(
        "/api/v1/analytics/events",
    )

    assert response.status_code == 200
    assert response.json() == []


async def test_event_analytics_groups_events_by_date(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Events should be counted by date and returned chronologically."""

    today = datetime.utcnow().replace(
        hour=12,
        minute=0,
        second=0,
        microsecond=0,
    )
    yesterday = today - timedelta(days=1)

    db_session.add_all(
        [
            SecurityEvent(
                event_type="ANALYTICS_YESTERDAY",
                severity=EventSeverity.INFO,
                source="pytest",
                message="Yesterday event.",
                created_at=yesterday,
            ),
            SecurityEvent(
                event_type="ANALYTICS_TODAY_ONE",
                severity=EventSeverity.WARNING,
                source="pytest",
                message="First today event.",
                created_at=today,
            ),
            SecurityEvent(
                event_type="ANALYTICS_TODAY_TWO",
                severity=EventSeverity.CRITICAL,
                source="pytest",
                message="Second today event.",
                created_at=today + timedelta(minutes=1),
            ),
        ]
    )

    await db_session.flush()

    response = await viewer_client.get(
        "/api/v1/analytics/events",
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "date": yesterday.date().isoformat(),
            "count": 1,
        },
        {
            "date": today.date().isoformat(),
            "count": 2,
        },
    ]
