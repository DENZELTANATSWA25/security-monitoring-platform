"""Integration tests for the incident API."""

from httpx import AsyncClient

from app.models.security_event import SecurityEvent


async def test_unauthenticated_user_cannot_list_incidents(
    client: AsyncClient,
) -> None:
    """Incident information must not be exposed without authentication."""

    response = await client.get("/api/v1/incidents/")

    assert response.status_code == 401


async def test_unauthenticated_user_cannot_read_incident(
    client: AsyncClient,
) -> None:
    """A single incident must not be exposed without authentication."""

    response = await client.get("/api/v1/incidents/999999")

    assert response.status_code == 401


async def test_viewer_cannot_create_incident(
    viewer_client: AsyncClient,
    security_event: SecurityEvent,
) -> None:
    """Viewers must not be allowed to create incidents."""

    response = await viewer_client.post(
        "/api/v1/incidents/",
        json={
            "title": "Viewer-created incident",
            "description": "This request must be rejected.",
            "severity": "WARNING",
            "event_id": security_event.id,
        },
    )

    assert response.status_code == 403


async def test_analyst_can_create_incident(
    analyst_client: AsyncClient,
    security_event: SecurityEvent,
) -> None:
    """Analysts should be able to create incidents."""

    response = await analyst_client.post(
        "/api/v1/incidents/",
        json={
            "title": "Suspicious authentication activity",
            "description": "Multiple suspicious authentication attempts detected.",
            "severity": "WARNING",
            "event_id": security_event.id,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == "Suspicious authentication activity"
    assert body["description"] == (
        "Multiple suspicious authentication attempts detected."
    )
    assert body["severity"] == "WARNING"
    assert body["status"] == "OPEN"
    assert body["event_id"] == security_event.id
    assert body["assigned_user_id"] is None


async def test_admin_can_create_incident(
    admin_client: AsyncClient,
    security_event: SecurityEvent,
) -> None:
    """Administrators should be able to create incidents."""

    response = await admin_client.post(
        "/api/v1/incidents/",
        json={
            "title": "Critical security incident",
            "description": "Critical activity requires investigation.",
            "severity": "CRITICAL",
            "event_id": security_event.id,
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "OPEN"


async def test_authenticated_user_can_list_incidents(
    viewer_client: AsyncClient,
) -> None:
    """Authenticated viewers should be able to read the incident list."""

    response = await viewer_client.get("/api/v1/incidents/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


async def test_missing_incident_returns_404(
    viewer_client: AsyncClient,
) -> None:
    """An authenticated request for an unknown incident should return 404."""

    response = await viewer_client.get(
        "/api/v1/incidents/999999",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"

async def test_incident_requires_originating_event(
        analyst_client: AsyncClient,
) -> None:
    """An incident must have an originating security event."""

    response = await analyst_client.post(
        "/api/v1/incidents/",
        json={
            "title": "Test incident",
            "description": "This request  intentionally omits event_id.",
            "severity": "HIGH",
        },
    )

    assert response.status_code == 422