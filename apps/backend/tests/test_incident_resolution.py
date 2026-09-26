"""Integration tests for incident resolution behaviour."""

from httpx import AsyncClient

from app.models.incident import Incident


async def test_analyst_can_create_and_read_resolution(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "TRUE_POSITIVE",
            "summary": "Confirmed malicious activity.",
            "root_cause": "Compromised credentials.",
            "remediation": "Credentials rotated.",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["incident_id"] == incident.id
    assert body["classification"] == "TRUE_POSITIVE"
    assert body["summary"] == "Confirmed malicious activity."

    get_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/resolution",
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]


async def test_resolution_can_be_updated(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    first_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "INCONCLUSIVE",
            "summary": "Investigation still uncertain.",
        },
    )

    assert first_response.status_code == 200

    update_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "TRUE_POSITIVE",
            "summary": "Further investigation confirmed malicious activity.",
            "root_cause": "Credential compromise.",
            "remediation": "Account secured.",
        },
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["classification"] == "TRUE_POSITIVE"
    assert body["summary"] == (
        "Further investigation confirmed malicious activity."
    )


async def test_resolution_update_creates_timeline_activity(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    create_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "INCONCLUSIVE",
            "summary": "Initial investigation.",
        },
    )

    assert create_response.status_code == 200

    update_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "FALSE_POSITIVE",
            "summary": "Activity determined to be legitimate.",
        },
    )

    assert update_response.status_code == 200

    timeline_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/activities",
    )

    assert timeline_response.status_code == 200

    activity_types = [
        activity["activity_type"]
        for activity in timeline_response.json()
    ]

    assert activity_types.count("RESOLUTION_ADDED") == 1
    assert activity_types.count("RESOLUTION_UPDATED") == 1


async def test_identical_resolution_put_is_no_op(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    """Submitting identical resolution data must not create audit noise."""

    payload = {
        "classification": "TRUE_POSITIVE",
        "summary": "Confirmed malicious activity.",
        "root_cause": "Compromised credentials.",
        "remediation": "Credentials rotated.",
    }

    first_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json=payload,
    )

    assert first_response.status_code == 200

    first_body = first_response.json()

    second_response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json=payload,
    )

    assert second_response.status_code == 200

    second_body = second_response.json()

    # The existing resolution should be returned rather than replaced.
    assert second_body["id"] == first_body["id"]

    # No-op updates must not modify the stored timestamp.
    assert second_body["updated_at"] == first_body["updated_at"]

    timeline_response = await analyst_client.get(
        f"/api/v1/incidents/{incident.id}/activities",
    )

    assert timeline_response.status_code == 200

    activity_types = [
        activity["activity_type"]
        for activity in timeline_response.json()
    ]

    assert activity_types.count("RESOLUTION_ADDED") == 1
    assert activity_types.count("RESOLUTION_UPDATED") == 0


async def test_resolution_summary_is_trimmed(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "BENIGN",
            "summary": "   Expected administrative activity.   ",
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] == (
        "Expected administrative activity."
    )


async def test_blank_resolution_summary_is_rejected(
    analyst_client: AsyncClient,
    incident: Incident,
) -> None:
    response = await analyst_client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "INCONCLUSIVE",
            "summary": "   ",
        },
    )

    assert response.status_code == 422


async def test_viewer_can_read_resolution(
    client: AsyncClient,
    analyst_token: str,
    viewer_token: str,
    incident: Incident,
) -> None:
    """Analysts may create resolutions and viewers may read them."""

    create_response = await client.put(
        f"/api/v1/incidents/{incident.id}/resolution",
        json={
            "classification": "BENIGN",
            "summary": "Expected system activity.",
        },
        headers={
            "Authorization": f"Bearer {analyst_token}",
        },
    )

    assert create_response.status_code == 200

    response = await client.get(
        f"/api/v1/incidents/{incident.id}/resolution",
        headers={
            "Authorization": f"Bearer {viewer_token}",
        },
    )

    assert response.status_code == 200
    assert response.json()["classification"] == "BENIGN"


async def test_missing_incident_resolution_returns_404(
    analyst_client: AsyncClient,
) -> None:
    response = await analyst_client.get(
        "/api/v1/incidents/999999/resolution",
    )

    assert response.status_code == 404
