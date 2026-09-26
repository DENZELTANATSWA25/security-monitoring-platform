"""Integration tests for incident investigation features."""

from httpx import AsyncClient

from app.models.alert import Alert
from app.models.incident import Incident
from app.models.security_event import SecurityEvent


async def test_analyst_can_add_and_read_note(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/notes",
        json={"content": "Investigating suspicious authentication activity."},
    )

    assert response.status_code == 200
    assert response.json()["content"] == (
        "Investigating suspicious authentication activity."
    )

    list_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/notes",
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_viewer_cannot_add_note(
    viewer_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await viewer_client.post(
        f"/api/v1/incidents/{incident.id}/notes",
        json={"content": "Viewer note"},
    )

    assert response.status_code == 403


async def test_blank_note_is_rejected(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/notes",
        json={"content": "   "},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Note content cannot be empty"


async def test_note_creates_timeline_activity(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    note_response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/notes",
        json={"content": "Timeline test note."},
    )

    assert note_response.status_code == 200

    timeline_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/activities",
    )

    assert timeline_response.status_code == 200

    activity_types = [
        activity["activity_type"]
        for activity in timeline_response.json()
    ]

    assert "NOTE_ADDED" in activity_types


async def test_analyst_can_add_and_read_evidence(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/evidence",
        json={
            "evidence_type": "IP_ADDRESS",
            "value": "203.0.113.10",
            "description": "Source address observed during investigation.",
            "source": "authentication-log",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["evidence_type"] == "IP_ADDRESS"
    assert body["value"] == "203.0.113.10"

    list_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/evidence",
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_viewer_cannot_add_evidence(
    viewer_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await viewer_client.post(
        f"/api/v1/incidents/{incident.id}/evidence",
        json={
            "evidence_type": "DOMAIN",
            "value": "example.test",
        },
    )

    assert response.status_code == 403


async def test_blank_evidence_value_is_rejected(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/evidence",
        json={
            "evidence_type": "IP_ADDRESS",
            "value": "   ",
        },
    )

    assert response.status_code == 422


async def test_evidence_creates_timeline_activity(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/evidence",
        json={
            "evidence_type": "FILE_HASH",
            "value": "abc123-test-hash",
        },
    )

    assert response.status_code == 201

    timeline_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/activities",
    )

    assert timeline_response.status_code == 200

    activity_types = [
        activity["activity_type"]
        for activity in timeline_response.json()
    ]

    assert "EVIDENCE_ADDED" in activity_types


async def test_analyst_can_link_additional_event(
    analyst_client: AsyncClient,
    incident: Incident,
    additional_security_event: SecurityEvent,
) -> None:
    response = await analyst_client.post(
        (
            f"/api/v1/incidents/{incident.id}"
            f"/events/{additional_security_event.id}"
        ),
    )

    assert response.status_code == 201
    assert response.json()["event_id"] == additional_security_event.id

    list_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/events",
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_originating_event_cannot_be_linked_again(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/events/{incident.event_id}",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Event is already the originating event for this incident."
    )


async def test_duplicate_event_link_is_rejected(
    analyst_client: AsyncClient,
    incident: Incident,
    additional_security_event: SecurityEvent,
) -> None:
    first_response = await analyst_client.post(
        (
            f"/api/v1/incidents/{incident.id}"
            f"/events/{additional_security_event.id}"
        ),
    )

    assert first_response.status_code == 201

    second_response = await analyst_client.post(
        (
            f"/api/v1/incidents/{incident.id}"
            f"/events/{additional_security_event.id}"
        ),
    )

    assert second_response.status_code == 409


async def test_viewer_cannot_link_event(
    viewer_client: AsyncClient,
    incident: Incident,
    additional_security_event: SecurityEvent,
) -> None:
    response = await viewer_client.post(
        (
            f"/api/v1/incidents/{incident.id}"
            f"/events/{additional_security_event.id}"
        ),
    )

    assert response.status_code == 403


async def test_analyst_can_link_alert(
    analyst_client: AsyncClient,
    incident: Incident,
    alert: Alert,
) -> None:
    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/alerts/{alert.id}",
    )

    assert response.status_code == 201
    assert response.json()["alert_id"] == alert.id

    list_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/alerts",
    )

    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


async def test_duplicate_alert_link_is_rejected(
    analyst_client: AsyncClient,
    incident: Incident,
    alert: Alert,
) -> None:
    first_response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/alerts/{alert.id}",
    )

    assert first_response.status_code == 201

    second_response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/alerts/{alert.id}",
    )

    assert second_response.status_code == 409


async def test_viewer_cannot_link_alert(
    viewer_client: AsyncClient,
    incident: Incident,
    alert: Alert,
) -> None:
    response = await viewer_client.post(
        f"/api/v1/incidents/{incident.id}/alerts/{alert.id}",
    )

    assert response.status_code == 403


async def test_linking_event_and_alert_creates_timeline_activity(
    analyst_client: AsyncClient,
    incident: Incident,
    additional_security_event: SecurityEvent,
    alert: Alert,
) -> None:
    event_response = await analyst_client.post(
        (
            f"/api/v1/incidents/{incident.id}"
            f"/events/{additional_security_event.id}"
        ),
    )

    assert event_response.status_code == 201

    alert_response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/alerts/{alert.id}",
    )

    assert alert_response.status_code == 201

    timeline_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/activities",
    )

    assert timeline_response.status_code == 200

    activity_types = [
        activity["activity_type"]
        for activity in timeline_response.json()
    ]

    assert "EVENT_LINKED" in activity_types
    assert "ALERT_LINKED" in activity_types
