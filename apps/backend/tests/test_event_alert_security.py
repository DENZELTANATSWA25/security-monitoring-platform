"""Security and RBAC tests for security events and alerts."""

from httpx import AsyncClient

from app.models.alert import Alert
from app.models.security_event import SecurityEvent


async def test_unauthenticated_user_cannot_list_events(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/events/")

    assert response.status_code == 401


async def test_authenticated_viewer_can_list_events(
    viewer_client: AsyncClient,
    security_event: SecurityEvent,
) -> None:
    response = await viewer_client.get("/api/v1/events/")

    assert response.status_code == 200

    body = response.json()

    assert any(
        event["id"] == security_event.id
        for event in body
    )


async def test_unauthenticated_user_cannot_list_alerts(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/alerts/")

    assert response.status_code == 401


async def test_unauthenticated_user_cannot_read_alert(
    client: AsyncClient,
    alert: Alert,
) -> None:
    response = await client.get(
        f"/api/v1/alerts/{alert.id}",
    )

    assert response.status_code == 401


async def test_authenticated_viewer_can_list_alerts(
    viewer_client: AsyncClient,
    alert: Alert,
) -> None:
    response = await viewer_client.get("/api/v1/alerts/")

    assert response.status_code == 200

    body = response.json()

    assert any(
        item["id"] == alert.id
        for item in body
    )


async def test_authenticated_viewer_can_read_alert(
    viewer_client: AsyncClient,
    alert: Alert,
) -> None:
    response = await viewer_client.get(
        f"/api/v1/alerts/{alert.id}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == alert.id


async def test_viewer_cannot_resolve_alert(
    viewer_client: AsyncClient,
    alert: Alert,
) -> None:
    response = await viewer_client.patch(
        f"/api/v1/alerts/{alert.id}/resolve",
    )

    assert response.status_code == 403


async def test_analyst_can_resolve_alert(
    analyst_client: AsyncClient,
    alert: Alert,
) -> None:
    response = await analyst_client.patch(
        f"/api/v1/alerts/{alert.id}/resolve",
    )

    assert response.status_code == 200
    assert response.json()["resolved"] is True


async def test_resolving_missing_alert_returns_404(
    analyst_client: AsyncClient,
) -> None:
    response = await analyst_client.patch(
        "/api/v1/alerts/999999/resolve",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Alert not found"


async def test_direct_event_creation_endpoint_is_not_available(
    viewer_client: AsyncClient,
) -> None:
    """
    Security events must enter through the dedicated telemetry
    ingestion boundary rather than the human-facing events API.
    """

    response = await viewer_client.post(
        "/api/v1/events/",
        json={
            "event_type": "DIRECT_EVENT",
            "severity": "INFO",
            "source": "pytest",
            "description": "Direct event creation should not be available.",
        },
    )

    assert response.status_code == 405