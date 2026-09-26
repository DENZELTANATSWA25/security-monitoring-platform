"""Regression tests for incident assignment and lifecycle rules."""

from httpx import AsyncClient

from app.models.incident import Incident
from app.models.user import User


async def test_viewer_cannot_assign_incident(
    viewer_client: AsyncClient,
    incident: Incident,
    analyst_user: User,
) -> None:
    """Viewers must not be allowed to assign incidents."""

    response = await viewer_client.patch(
        f"/api/v1/incidents/{incident.id}/assign",
        json={"user_id": analyst_user.id},
    )

    assert response.status_code == 403


async def test_assigning_open_incident_starts_investigation(
    admin_client: AsyncClient,
    incident: Incident,
    analyst_user: User,
) -> None:
    """Assigning an OPEN incident should move it to IN_PROGRESS."""

    response = await admin_client.patch(
        f"/api/v1/incidents/{incident.id}/assign",
        json={"user_id": analyst_user.id},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["assigned_user_id"] == analyst_user.id
    assert body["assigned_to"] == analyst_user.full_name
    assert body["status"] == "IN_PROGRESS"


async def test_viewer_cannot_change_incident_status(
    viewer_client: AsyncClient,
    incident: Incident,
) -> None:
    """Viewers must not be allowed to change lifecycle state."""

    response = await viewer_client.patch(
        f"/api/v1/incidents/{incident.id}/status/IN_PROGRESS",
    )

    assert response.status_code == 403


async def test_open_incident_can_move_to_in_progress(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """OPEN -> IN_PROGRESS is a valid lifecycle transition."""

    response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/IN_PROGRESS",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


async def test_incident_cannot_close_directly_from_open(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """OPEN -> CLOSED must be rejected."""

    response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/CLOSED",
    )

    assert response.status_code == 409
    assert "cannot transition" in response.json()["detail"]


async def test_incident_cannot_resolve_without_resolution(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """An incident needs documented resolution before becoming RESOLVED."""

    response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/RESOLVED",
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "Incident resolution required before resolving incident"
    )


async def test_same_status_is_idempotent(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """Requesting the current status should succeed without changing state."""

    response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/OPEN",
    )

    assert response.status_code == 200
    assert response.json()["status"] == "OPEN"


async def test_assigning_unknown_user_returns_404(
    admin_client: AsyncClient,
    incident: Incident,
) -> None:
    """Assignment to a nonexistent user should be rejected."""

    response = await admin_client.patch(
        f"/api/v1/incidents/{incident.id}/assign",
        json={"user_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Assigned user not found"


async def test_viewer_cannot_be_assigned_incident(
    admin_client: AsyncClient,
    incident: Incident,
    viewer_user: User,
) -> None:
    """Only administrators and analysts may receive incident assignments."""

    response = await admin_client.patch(
        f"/api/v1/incidents/{incident.id}/assign",
        json={"user_id": viewer_user.id},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Only administrators or analysts can be assigned to incidents"
    )


async def test_documented_resolution_allows_incident_to_be_resolved(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """A documented resolution should permit OPEN -> RESOLVED."""

    resolution_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "TRUE_POSITIVE",
            "summary": "Confirmed malicious authentication activity.",
            "root_cause": "Compromised user credentials.",
            "remediation": "Credentials rotated and sessions revoked.",
        },
    )

    assert resolution_response.status_code == 200

    status_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/RESOLVED",
    )

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "RESOLVED"


async def test_resolved_incident_can_be_closed(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """RESOLVED -> CLOSED is a valid lifecycle transition."""

    resolution_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "TRUE_POSITIVE",
            "summary": "Investigation completed.",
            "root_cause": "Compromised credentials.",
            "remediation": "Account secured.",
        },
    )

    assert resolution_response.status_code == 200

    resolved_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/RESOLVED",
    )

    assert resolved_response.status_code == 200

    closed_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/CLOSED",
    )

    assert closed_response.status_code == 200
    assert closed_response.json()["status"] == "CLOSED"


async def test_closed_incident_can_be_explicitly_reopened(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """A CLOSED incident may explicitly transition back to IN_PROGRESS."""

    resolution_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "TRUE_POSITIVE",
            "summary": "Investigation completed.",
        },
    )

    assert resolution_response.status_code == 200

    resolved_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/RESOLVED",
    )

    assert resolved_response.status_code == 200

    closed_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/CLOSED",
    )

    assert closed_response.status_code == 200

    reopened_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/IN_PROGRESS",
    )

    assert reopened_response.status_code == 200
    assert reopened_response.json()["status"] == "IN_PROGRESS"


async def test_assignment_does_not_reopen_closed_incident(
    admin_client: AsyncClient,
    incident: Incident,
    analyst_user: User,
) -> None:
    """Assigning a CLOSED incident must not implicitly reopen it."""

    resolution_response = await admin_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "TRUE_POSITIVE",
            "summary": "Investigation completed.",
        },
    )

    assert resolution_response.status_code == 200

    resolved_response = await admin_client.patch(
        f"/api/v1/incidents/{incident.id}/status/RESOLVED",
    )

    assert resolved_response.status_code == 200

    closed_response = await admin_client.patch(
        f"/api/v1/incidents/{incident.id}/status/CLOSED",
    )

    assert closed_response.status_code == 200

    assignment_response = await admin_client.patch(
        f"/api/v1/incidents/{incident.id}/assign",
        json={
            "user_id": analyst_user.id,
        },
    )

    assert assignment_response.status_code == 200

    body = assignment_response.json()

    assert body["assigned_user_id"] == analyst_user.id
    assert body["status"] == "CLOSED"


async def test_viewer_cannot_add_incident_resolution(
    viewer_client: AsyncClient,
    incident: Incident,
) -> None:
    """Viewers must not be allowed to document incident resolutions."""

    response = await viewer_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "BENIGN",
            "summary": "Benign activity.",
        },
    )

    assert response.status_code == 403


async def test_lifecycle_changes_are_recorded_in_activity_timeline(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """Important lifecycle actions should leave an auditable timeline."""

    resolution_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "TRUE_POSITIVE",
            "summary": "Confirmed security incident.",
        },
    )

    assert resolution_response.status_code == 200

    resolved_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/RESOLVED",
    )

    assert resolved_response.status_code == 200

    closed_response = await analyst_client.patch(
        f"/api/v1/incidents/{incident.id}/status/CLOSED",
    )

    assert closed_response.status_code == 200

    timeline_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/activities",
    )

    assert timeline_response.status_code == 200

    activities = timeline_response.json()

    activity_types = [
        activity["activity_type"]
        for activity in activities
    ]

    assert "RESOLUTION_ADDED" in activity_types
    assert activity_types.count("STATUS_CHANGED") == 2
