"""Integration tests for incident querying."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import Incident, IncidentStatus


pytestmark = pytest.mark.asyncio


async def create_test_incident(
    db_session: AsyncSession,
    *,
    event_id: int,
    title: str,
    description: str,
    severity: str,
    status: IncidentStatus,
    created_at: datetime,
    assigned_user_id: int | None = None,
    assigned_to: str | None = None,
) -> Incident:
    """Create an incident with predictable query-test data."""

    incident = Incident(
        title=title,
        description=description,
        severity=severity,
        status=status,
        assigned_user_id=assigned_user_id,
        assigned_to=assigned_to,
        event_id=event_id,
        created_at=created_at,
        updated_at=created_at,
    )

    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    return incident


async def test_incidents_are_paginated(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
) -> None:
    base_time = datetime(2026, 10, 1, 12, 0, 0)

    for index in range(3):
        await create_test_incident(
            db_session,
            event_id=security_event.id,
            title=f"Pagination Incident {index}",
            description=f"Pagination test incident {index}",
            severity="LOW",
            status=IncidentStatus.OPEN,
            created_at=base_time + timedelta(minutes=index),
        )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "search": "Pagination Incident",
            "limit": 2,
            "offset": 1,
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    incidents = response.json()

    assert len(incidents) == 2
    assert incidents[0]["title"] == "Pagination Incident 1"
    assert incidents[1]["title"] == "Pagination Incident 2"


async def test_incidents_can_be_filtered_by_status(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
) -> None:
    now = datetime(2026, 10, 2, 12, 0, 0)

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Open Status Query Incident",
        description="Status query test",
        severity="HIGH",
        status=IncidentStatus.OPEN,
        created_at=now,
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Closed Status Query Incident",
        description="Status query test",
        severity="HIGH",
        status=IncidentStatus.CLOSED,
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "status": "OPEN",
            "search": "Status Query Incident",
        },
    )

    assert response.status_code == 200

    incidents = response.json()

    assert len(incidents) == 1
    assert incidents[0]["title"] == "Open Status Query Incident"
    assert incidents[0]["status"] == "OPEN"


async def test_incidents_can_be_filtered_by_severity(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
) -> None:
    now = datetime(2026, 10, 3, 12, 0, 0)

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Low Severity Query Incident",
        description="Severity query test",
        severity="LOW",
        status=IncidentStatus.OPEN,
        created_at=now,
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Critical Severity Query Incident",
        description="Severity query test",
        severity="CRITICAL",
        status=IncidentStatus.OPEN,
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "severity": "CRITICAL",
            "search": "Severity Query Incident",
        },
    )

    assert response.status_code == 200

    incidents = response.json()

    assert len(incidents) == 1
    assert incidents[0]["title"] == "Critical Severity Query Incident"


async def test_incidents_can_be_filtered_by_assigned_user(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
    analyst_user,
    admin_user,
) -> None:
    now = datetime(2026, 10, 4, 12, 0, 0)

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Analyst Assigned Query Incident",
        description="Assignment query test",
        severity="HIGH",
        status=IncidentStatus.IN_PROGRESS,
        assigned_user_id=analyst_user.id,
        assigned_to=analyst_user.full_name,
        created_at=now,
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Admin Assigned Query Incident",
        description="Assignment query test",
        severity="HIGH",
        status=IncidentStatus.IN_PROGRESS,
        assigned_user_id=admin_user.id,
        assigned_to=admin_user.full_name,
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "assigned_user_id": analyst_user.id,
            "search": "Assigned Query Incident",
        },
    )

    assert response.status_code == 200

    incidents = response.json()

    assert len(incidents) == 1
    assert incidents[0]["assigned_user_id"] == analyst_user.id


async def test_incidents_can_be_filtered_as_unassigned(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
    analyst_user,
) -> None:
    now = datetime(2026, 10, 5, 12, 0, 0)

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Unassigned Query Incident",
        description="Unassigned query test",
        severity="HIGH",
        status=IncidentStatus.OPEN,
        created_at=now,
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Assigned Comparison Query Incident",
        description="Unassigned query test",
        severity="HIGH",
        status=IncidentStatus.IN_PROGRESS,
        assigned_user_id=analyst_user.id,
        assigned_to=analyst_user.full_name,
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "unassigned": "true",
            "search": "query test",
        },
    )

    assert response.status_code == 200

    incidents = response.json()

    assert len(incidents) == 1
    assert incidents[0]["title"] == "Unassigned Query Incident"
    assert incidents[0]["assigned_user_id"] is None


@pytest.mark.parametrize(
    ("search", "expected_title"),
    [
        ("Searchable Incident Title", "Searchable Incident Title"),
        ("suspicious persistence", "Description Search Incident"),
        ("critical", "Severity Search Incident"),
        ("Query Analyst Name", "Assignee Search Incident"),
    ],
)
async def test_incidents_can_be_searched_across_text_fields(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
    search: str,
    expected_title: str,
) -> None:
    now = datetime(2026, 10, 6, 12, 0, 0)

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Searchable Incident Title",
        description="First incident description",
        severity="LOW",
        status=IncidentStatus.OPEN,
        created_at=now,
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Description Search Incident",
        description="Suspicious persistence mechanism detected",
        severity="MEDIUM",
        status=IncidentStatus.OPEN,
        created_at=now + timedelta(minutes=1),
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Severity Search Incident",
        description="Third incident description",
        severity="CRITICAL",
        status=IncidentStatus.OPEN,
        created_at=now + timedelta(minutes=2),
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Assignee Search Incident",
        description="Fourth incident description",
        severity="HIGH",
        status=IncidentStatus.IN_PROGRESS,
        assigned_to="Query Analyst Name",
        created_at=now + timedelta(minutes=3),
    )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={"search": search},
    )

    assert response.status_code == 200

    titles = {
        incident["title"]
        for incident in response.json()
    }

    assert expected_title in titles


async def test_incident_search_is_case_insensitive(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
) -> None:
    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Case Insensitive Incident",
        description="Suspicious PowerShell execution detected",
        severity="HIGH",
        status=IncidentStatus.OPEN,
        created_at=datetime(2026, 10, 6, 16, 0, 0),
    )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={"search": "powershell"},
    )

    assert response.status_code == 200

    titles = {
        incident["title"]
        for incident in response.json()
    }

    assert "Case Insensitive Incident" in titles


async def test_incidents_can_be_filtered_by_date_range(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
) -> None:
    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Incident Before Range",
        description="Date range incident test",
        severity="LOW",
        status=IncidentStatus.OPEN,
        created_at=datetime(2026, 9, 30, 12, 0, 0),
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Incident Inside Range",
        description="Date range incident test",
        severity="HIGH",
        status=IncidentStatus.OPEN,
        created_at=datetime(2026, 10, 3, 12, 0, 0),
    )

    await create_test_incident(
        db_session,
        event_id=security_event.id,
        title="Incident After Range",
        description="Date range incident test",
        severity="LOW",
        status=IncidentStatus.OPEN,
        created_at=datetime(2026, 10, 8, 12, 0, 0),
    )

    response = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "search": "Date range incident test",
            "start_date": "2026-10-01T00:00:00",
            "end_date": "2026-10-07T23:59:59",
        },
    )

    assert response.status_code == 200

    incidents = response.json()

    assert len(incidents) == 1
    assert incidents[0]["title"] == "Incident Inside Range"


async def test_incidents_support_ascending_and_descending_order(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    security_event,
) -> None:
    base_time = datetime(2026, 10, 7, 12, 0, 0)

    for index in range(3):
        await create_test_incident(
            db_session,
            event_id=security_event.id,
            title=f"Ordering Incident {index}",
            description=f"Ordering incident test {index}",
            severity="LOW",
            status=IncidentStatus.OPEN,
            created_at=base_time + timedelta(minutes=index),
        )

    ascending = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "search": "Ordering Incident",
            "sort_order": "asc",
        },
    )

    descending = await viewer_client.get(
        "/api/v1/incidents/",
        params={
            "search": "Ordering Incident",
            "sort_order": "desc",
        },
    )

    assert ascending.status_code == 200
    assert descending.status_code == 200

    assert [
        incident["title"]
        for incident in ascending.json()
    ] == [
        "Ordering Incident 0",
        "Ordering Incident 1",
        "Ordering Incident 2",
    ]

    assert [
        incident["title"]
        for incident in descending.json()
    ] == [
        "Ordering Incident 2",
        "Ordering Incident 1",
        "Ordering Incident 0",
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"status": "NOT_A_STATUS"},
        {"severity": ""},
        {"assigned_user_id": 0},
        {"unassigned": "not-a-boolean"},
        {"search": ""},
        {"sort_order": "random"},
    ],
)
async def test_invalid_incident_query_parameters_are_rejected(
    viewer_client: AsyncClient,
    params: dict,
) -> None:
    response = await viewer_client.get(
        "/api/v1/incidents/",
        params=params,
    )

    assert response.status_code == 422