"""Integration tests for security-event querying."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventSeverity, SecurityEvent


pytestmark = pytest.mark.asyncio


async def create_test_event(
    db_session: AsyncSession,
    *,
    event_type: str,
    severity: EventSeverity,
    source: str,
    message: str,
    created_at: datetime,
) -> SecurityEvent:
    """Create a security event with predictable query-test data."""

    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        source=source,
        message=message,
        created_at=created_at,
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    return event


async def test_events_are_paginated(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    base_time = datetime(2026, 10, 1, 12, 0, 0)

    for index in range(3):
        await create_test_event(
            db_session,
            event_type=f"PAGINATION_EVENT_{index}",
            severity=EventSeverity.INFO,
            source="pagination-test",
            message=f"Pagination event {index}",
            created_at=base_time + timedelta(minutes=index),
        )

    response = await viewer_client.get(
        "/api/v1/events/",
        params={
            "source": "pagination-test",
            "limit": 2,
            "offset": 1,
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 2
    assert events[0]["event_type"] == "PAGINATION_EVENT_1"
    assert events[1]["event_type"] == "PAGINATION_EVENT_2"


async def test_events_can_be_filtered_by_severity(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(2026, 10, 2, 12, 0, 0)

    await create_test_event(
        db_session,
        event_type="INFO_FILTER_EVENT",
        severity=EventSeverity.INFO,
        source="severity-filter-test",
        message="Informational event",
        created_at=now,
    )

    await create_test_event(
        db_session,
        event_type="CRITICAL_FILTER_EVENT",
        severity=EventSeverity.CRITICAL,
        source="severity-filter-test",
        message="Critical event",
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/events/",
        params={
            "source": "severity-filter-test",
            "severity": "CRITICAL",
        },
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1
    assert events[0]["event_type"] == "CRITICAL_FILTER_EVENT"
    assert events[0]["severity"] == "CRITICAL"


async def test_events_can_be_filtered_by_event_type(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(2026, 10, 3, 12, 0, 0)

    await create_test_event(
        db_session,
        event_type="LOGIN_FAILURE",
        severity=EventSeverity.WARNING,
        source="event-type-test",
        message="Failed login",
        created_at=now,
    )

    await create_test_event(
        db_session,
        event_type="FILE_ACCESS",
        severity=EventSeverity.INFO,
        source="event-type-test",
        message="File accessed",
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/events/",
        params={
            "event_type": "LOGIN_FAILURE",
            "source": "event-type-test",
        },
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1
    assert events[0]["event_type"] == "LOGIN_FAILURE"


async def test_events_can_be_filtered_by_source(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(2026, 10, 4, 12, 0, 0)

    await create_test_event(
        db_session,
        event_type="SOURCE_TEST",
        severity=EventSeverity.INFO,
        source="firewall-alpha",
        message="Firewall event",
        created_at=now,
    )

    await create_test_event(
        db_session,
        event_type="SOURCE_TEST",
        severity=EventSeverity.INFO,
        source="server-beta",
        message="Server event",
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/events/",
        params={"source": "firewall-alpha"},
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1
    assert events[0]["source"] == "firewall-alpha"


@pytest.mark.parametrize(
    ("search", "expected_type"),
    [
        ("MALWARE_SIGNATURE", "MALWARE_SIGNATURE"),
        ("endpoint-gamma", "SEARCH_SOURCE_EVENT"),
        ("suspicious executable", "SEARCH_MESSAGE_EVENT"),
    ],
)
async def test_events_can_be_searched_across_text_fields(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    search: str,
    expected_type: str,
) -> None:
    now = datetime(2026, 10, 5, 12, 0, 0)

    await create_test_event(
        db_session,
        event_type="MALWARE_SIGNATURE",
        severity=EventSeverity.CRITICAL,
        source="search-source-one",
        message="First search event",
        created_at=now,
    )

    await create_test_event(
        db_session,
        event_type="SEARCH_SOURCE_EVENT",
        severity=EventSeverity.WARNING,
        source="endpoint-gamma",
        message="Second search event",
        created_at=now + timedelta(minutes=1),
    )

    await create_test_event(
        db_session,
        event_type="SEARCH_MESSAGE_EVENT",
        severity=EventSeverity.WARNING,
        source="search-source-three",
        message="Suspicious executable detected",
        created_at=now + timedelta(minutes=2),
    )

    response = await viewer_client.get(
        "/api/v1/events/",
        params={"search": search},
    )

    assert response.status_code == 200

    event_types = {
        event["event_type"]
        for event in response.json()
    }

    assert expected_type in event_types


async def test_event_search_is_case_insensitive(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_test_event(
        db_session,
        event_type="CASE_INSENSITIVE_EVENT",
        severity=EventSeverity.WARNING,
        source="case-search-test",
        message="Suspicious PowerShell Activity",
        created_at=datetime(2026, 10, 5, 15, 0, 0),
    )

    response = await viewer_client.get(
        "/api/v1/events/",
        params={"search": "powershell"},
    )

    assert response.status_code == 200

    event_types = {
        event["event_type"]
        for event in response.json()
    }

    assert "CASE_INSENSITIVE_EVENT" in event_types


async def test_events_can_be_filtered_by_date_range(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_test_event(
        db_session,
        event_type="BEFORE_RANGE",
        severity=EventSeverity.INFO,
        source="date-range-test",
        message="Before range",
        created_at=datetime(2026, 9, 30, 12, 0, 0),
    )

    await create_test_event(
        db_session,
        event_type="INSIDE_RANGE",
        severity=EventSeverity.WARNING,
        source="date-range-test",
        message="Inside range",
        created_at=datetime(2026, 10, 3, 12, 0, 0),
    )

    await create_test_event(
        db_session,
        event_type="AFTER_RANGE",
        severity=EventSeverity.INFO,
        source="date-range-test",
        message="After range",
        created_at=datetime(2026, 10, 8, 12, 0, 0),
    )

    response = await viewer_client.get(
        "/api/v1/events/",
        params={
            "source": "date-range-test",
            "start_date": "2026-10-01T00:00:00",
            "end_date": "2026-10-07T23:59:59",
        },
    )

    assert response.status_code == 200

    events = response.json()

    assert len(events) == 1
    assert events[0]["event_type"] == "INSIDE_RANGE"


async def test_events_support_ascending_and_descending_order(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    base_time = datetime(2026, 10, 6, 12, 0, 0)

    for index in range(3):
        await create_test_event(
            db_session,
            event_type=f"ORDER_EVENT_{index}",
            severity=EventSeverity.INFO,
            source="ordering-test",
            message=f"Ordering event {index}",
            created_at=base_time + timedelta(minutes=index),
        )

    ascending = await viewer_client.get(
        "/api/v1/events/",
        params={
            "source": "ordering-test",
            "sort_order": "asc",
        },
    )

    descending = await viewer_client.get(
        "/api/v1/events/",
        params={
            "source": "ordering-test",
            "sort_order": "desc",
        },
    )

    assert ascending.status_code == 200
    assert descending.status_code == 200

    assert [
        event["event_type"]
        for event in ascending.json()
    ] == [
        "ORDER_EVENT_0",
        "ORDER_EVENT_1",
        "ORDER_EVENT_2",
    ]

    assert [
        event["event_type"]
        for event in descending.json()
    ] == [
        "ORDER_EVENT_2",
        "ORDER_EVENT_1",
        "ORDER_EVENT_0",
    ]


@pytest.mark.parametrize(
    ("params", "expected_status"),
    [
        ({"limit": 0}, 422),
        ({"limit": 101}, 422),
        ({"offset": -1}, 422),
        ({"severity": "NOT_A_SEVERITY"}, 422),
        ({"sort_order": "random"}, 422),
        ({"event_type": ""}, 422),
        ({"source": ""}, 422),
        ({"search": ""}, 422),
    ],
)
async def test_invalid_event_query_parameters_are_rejected(
    viewer_client: AsyncClient,
    params: dict,
    expected_status: int,
) -> None:
    response = await viewer_client.get(
        "/api/v1/events/",
        params=params,
    )

    assert response.status_code == expected_status