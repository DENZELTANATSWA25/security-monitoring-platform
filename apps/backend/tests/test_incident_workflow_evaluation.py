"""Phase 6D: incident workflow integrity and traceability evaluation."""

from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.incident import Incident
from app.models.incident_activity import IncidentActivity
from app.models.incident_evidence import EvidenceType, IncidentEvidence
from app.models.incident_note import IncidentNote
from app.models.security_event import SecurityEvent
from app.models.user import User
from app.services.incident_evidence_service import create_incident_evidence
from app.services.incident_note_service import create_incident_note

pytestmark = pytest.mark.asyncio


async def count_rows(db: AsyncSession, model, incident_id: int) -> int:
    """Count investigation records belonging to one incident."""
    result = await db.execute(
        select(func.count())
        .select_from(model)
        .where(model.incident_id == incident_id)
    )
    return result.scalar_one()


async def failed_activity(*args, **kwargs):
    """Simulate timeline creation failing after the record is flushed."""
    raise RuntimeError("Synthetic incident activity failure")


async def test_note_failure_can_be_rolled_back(
    db_session: AsyncSession,
    incident: Incident,
    analyst_user: User,
) -> None:
    """A failed timeline operation must not leave a persisted note."""

    incident_id = incident.id
    before = await count_rows(db_session, IncidentNote, incident_id)

    with patch(
        "app.services.incident_note_service.add_incident_activity",
        side_effect=failed_activity,
    ):
        with pytest.raises(RuntimeError, match="Synthetic"):
            await create_incident_note(
                db_session,
                incident_id=incident_id,
                author_user_id=analyst_user.id,
                content="Synthetic investigation note",
            )

    # The service does not explicitly roll back; the caller must do so.
    await db_session.rollback()

    after = await count_rows(db_session, IncidentNote, incident_id)

    assert after == before


async def test_evidence_failure_can_be_rolled_back(
    db_session: AsyncSession,
    incident: Incident,
    analyst_user: User,
) -> None:
    """A failed timeline operation must not leave persisted evidence."""

    incident_id = incident.id
    before = await count_rows(db_session, IncidentEvidence, incident_id)

    with patch(
        "app.services.incident_evidence_service.add_incident_activity",
        side_effect=failed_activity,
    ):
        with pytest.raises(RuntimeError, match="Synthetic"):
            await create_incident_evidence(
                db_session,
                incident_id=incident_id,
                evidence_type=EvidenceType.IP_ADDRESS,
                value="203.0.113.25",
                added_by_user_id=analyst_user.id,
                description="Synthetic failure-injection evidence",
            )

    await db_session.rollback()

    after = await count_rows(db_session, IncidentEvidence, incident_id)

    assert after == before


async def test_successful_note_has_exactly_one_activity(
    analyst_client: AsyncClient,
    db_session: AsyncSession,
    incident: Incident,
) -> None:
    """A successful note produces one note and one timeline entry."""

    before_notes = await count_rows(db_session, IncidentNote, incident.id)
    before_activities = await count_rows(
        db_session, IncidentActivity, incident.id
    )

    response = await analyst_client.post(
        f"/api/v1/incidents/{incident.id}/notes",
        json={"content": "Synthetic traceability evaluation note"},
    )

    assert response.status_code == 200
    assert (
        await count_rows(db_session, IncidentNote, incident.id)
        == before_notes + 1
    )
    assert (
        await count_rows(db_session, IncidentActivity, incident.id)
        == before_activities + 1
    )


async def test_duplicate_event_link_does_not_add_activity(
    analyst_client: AsyncClient,
    db_session: AsyncSession,
    incident: Incident,
    additional_security_event: SecurityEvent,
) -> None:
    """Rejecting a duplicate event link must not duplicate timeline entries."""

    url = (
        f"/api/v1/incidents/{incident.id}"
        f"/events/{additional_security_event.id}"
    )

    first = await analyst_client.post(url)
    assert first.status_code == 201

    activities_after_first = await count_rows(
        db_session, IncidentActivity, incident.id
    )

    second = await analyst_client.post(url)
    assert second.status_code == 409

    activities_after_second = await count_rows(
        db_session, IncidentActivity, incident.id
    )

    assert activities_after_second == activities_after_first


async def test_duplicate_alert_link_does_not_add_activity(
    analyst_client: AsyncClient,
    db_session: AsyncSession,
    incident: Incident,
    alert: Alert,
) -> None:
    """Rejecting a duplicate alert link must preserve timeline consistency."""

    url = f"/api/v1/incidents/{incident.id}/alerts/{alert.id}"

    first = await analyst_client.post(url)
    assert first.status_code == 201

    activities_after_first = await count_rows(
        db_session, IncidentActivity, incident.id
    )

    second = await analyst_client.post(url)
    assert second.status_code == 409

    activities_after_second = await count_rows(
        db_session, IncidentActivity, incident.id
    )

    assert activities_after_second == activities_after_first
