"""Integration tests for security-alert querying."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


pytestmark = pytest.mark.asyncio


async def create_test_alert(
    db_session: AsyncSession,
    *,
    alert_type: str,
    severity: str,
    message: str,
    resolved: bool,
    created_at: datetime,
) -> Alert:
    """Create an alert with predictable query-test data."""

    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        resolved=resolved,
        created_at=created_at,
    )

    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    return alert


async def test_alerts_are_paginated(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    base_time = datetime(
        2026, 10, 1, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    for index in range(3):
        await create_test_alert(
            db_session,
            alert_type=f"PAGINATION_ALERT_{index}",
            severity="LOW",
            message=f"Pagination alert {index}",
            resolved=False,
            created_at=base_time + timedelta(minutes=index),
        )

    response = await viewer_client.get(
        "/api/v1/alerts/",
        params={
            "search": "Pagination alert",
            "limit": 2,
            "offset": 1,
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    alerts = response.json()

    assert len(alerts) == 2
    assert alerts[0]["alert_type"] == "PAGINATION_ALERT_1"
    assert alerts[1]["alert_type"] == "PAGINATION_ALERT_2"


async def test_alerts_can_be_filtered_by_resolved_state(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(
        2026, 10, 2, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    await create_test_alert(
        db_session,
        alert_type="UNRESOLVED_FILTER_ALERT",
        severity="HIGH",
        message="Unresolved filter test",
        resolved=False,
        created_at=now,
    )

    await create_test_alert(
        db_session,
        alert_type="RESOLVED_FILTER_ALERT",
        severity="HIGH",
        message="Resolved filter test",
        resolved=True,
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/alerts/",
        params={
            "resolved": "false",
            "search": "filter test",
        },
    )

    assert response.status_code == 200

    alerts = response.json()

    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "UNRESOLVED_FILTER_ALERT"
    assert alerts[0]["resolved"] is False


async def test_alerts_can_be_filtered_by_severity(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(
        2026, 10, 3, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    await create_test_alert(
        db_session,
        alert_type="LOW_SEVERITY_ALERT",
        severity="LOW",
        message="Severity filter test low",
        resolved=False,
        created_at=now,
    )

    await create_test_alert(
        db_session,
        alert_type="CRITICAL_SEVERITY_ALERT",
        severity="CRITICAL",
        message="Severity filter test critical",
        resolved=False,
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/alerts/",
        params={
            "severity": "CRITICAL",
            "search": "Severity filter test",
        },
    )

    assert response.status_code == 200

    alerts = response.json()

    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "CRITICAL_SEVERITY_ALERT"


async def test_alerts_can_be_filtered_by_alert_type(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(
        2026, 10, 4, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    await create_test_alert(
        db_session,
        alert_type="BRUTE_FORCE_QUERY_TEST",
        severity="HIGH",
        message="Alert type query test one",
        resolved=False,
        created_at=now,
    )

    await create_test_alert(
        db_session,
        alert_type="EVENT_BURST_QUERY_TEST",
        severity="MEDIUM",
        message="Alert type query test two",
        resolved=False,
        created_at=now + timedelta(minutes=1),
    )

    response = await viewer_client.get(
        "/api/v1/alerts/",
        params={"alert_type": "BRUTE_FORCE_QUERY_TEST"},
    )

    assert response.status_code == 200

    alerts = response.json()

    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "BRUTE_FORCE_QUERY_TEST"


@pytest.mark.parametrize(
    ("search", "expected_type"),
    [
        ("SEARCH_ALERT_TYPE", "SEARCH_ALERT_TYPE"),
        ("critical", "SEARCH_SEVERITY_ALERT"),
        ("credential stuffing", "SEARCH_MESSAGE_ALERT"),
    ],
)
async def test_alerts_can_be_searched_across_text_fields(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
    search: str,
    expected_type: str,
) -> None:
    now = datetime(
        2026, 10, 5, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    await create_test_alert(
        db_session,
        alert_type="SEARCH_ALERT_TYPE",
        severity="LOW",
        message="First searchable alert",
        resolved=False,
        created_at=now,
    )

    await create_test_alert(
        db_session,
        alert_type="SEARCH_SEVERITY_ALERT",
        severity="CRITICAL",
        message="Second searchable alert",
        resolved=False,
        created_at=now + timedelta(minutes=1),
    )

    await create_test_alert(
        db_session,
        alert_type="SEARCH_MESSAGE_ALERT",
        severity="HIGH",
        message="Credential stuffing detected",
        resolved=False,
        created_at=now + timedelta(minutes=2),
    )

    response = await viewer_client.get(
        "/api/v1/alerts/",
        params={"search": search},
    )

    assert response.status_code == 200

    alert_types = {
        alert["alert_type"]
        for alert in response.json()
    }

    assert expected_type in alert_types


async def test_alert_search_is_case_insensitive(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_test_alert(
        db_session,
        alert_type="CASE_INSENSITIVE_ALERT",
        severity="HIGH",
        message="Suspicious PowerShell execution",
        resolved=False,
        created_at=datetime(
            2026, 10, 5, 15, 0, 0,
            tzinfo=timezone.utc,
        ),
    )

    response = await viewer_client.get(
        "/api/v1/alerts/",
        params={"search": "powershell"},
    )

    assert response.status_code == 200

    alert_types = {
        alert["alert_type"]
        for alert in response.json()
    }

    assert "CASE_INSENSITIVE_ALERT" in alert_types


async def test_alerts_can_be_filtered_by_date_range(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_test_alert(
        db_session,
        alert_type="ALERT_BEFORE_RANGE",
        severity="LOW",
        message="Date range alert test",
        resolved=False,
        created_at=datetime(
            2026, 9, 30, 12, 0, 0,
            tzinfo=timezone.utc,
        ),
    )

    await create_test_alert(
        db_session,
        alert_type="ALERT_INSIDE_RANGE",
        severity="HIGH",
        message="Date range alert test",
        resolved=False,
        created_at=datetime(
            2026, 10, 3, 12, 0, 0,
            tzinfo=timezone.utc,
        ),
    )

    await create_test_alert(
        db_session,
        alert_type="ALERT_AFTER_RANGE",
        severity="LOW",
        message="Date range alert test",
        resolved=False,
        created_at=datetime(
            2026, 10, 8, 12, 0, 0,
            tzinfo=timezone.utc,
        ),
    )

    response = await viewer_client.get(
        "/api/v1/alerts/",
        params={
            "search": "Date range alert test",
            "start_date": "2026-10-01T00:00:00Z",
            "end_date": "2026-10-07T23:59:59Z",
        },
    )

    assert response.status_code == 200

    alerts = response.json()

    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "ALERT_INSIDE_RANGE"


async def test_alerts_support_ascending_and_descending_order(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    base_time = datetime(
        2026, 10, 6, 12, 0, 0,
        tzinfo=timezone.utc,
    )

    for index in range(3):
        await create_test_alert(
            db_session,
            alert_type=f"ORDER_ALERT_{index}",
            severity="LOW",
            message=f"Ordering alert {index}",
            resolved=False,
            created_at=base_time + timedelta(minutes=index),
        )

    ascending = await viewer_client.get(
        "/api/v1/alerts/",
        params={
            "search": "Ordering alert",
            "sort_order": "asc",
        },
    )

    descending = await viewer_client.get(
        "/api/v1/alerts/",
        params={
            "search": "Ordering alert",
            "sort_order": "desc",
        },
    )

    assert ascending.status_code == 200
    assert descending.status_code == 200

    assert [
        alert["alert_type"]
        for alert in ascending.json()
    ] == [
        "ORDER_ALERT_0",
        "ORDER_ALERT_1",
        "ORDER_ALERT_2",
    ]

    assert [
        alert["alert_type"]
        for alert in descending.json()
    ] == [
        "ORDER_ALERT_2",
        "ORDER_ALERT_1",
        "ORDER_ALERT_0",
    ]


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"sort_order": "random"},
        {"severity": ""},
        {"alert_type": ""},
        {"search": ""},
        {"resolved": "not-a-boolean"},
    ],
)
async def test_invalid_alert_query_parameters_are_rejected(
    viewer_client: AsyncClient,
    params: dict,
) -> None:
    response = await viewer_client.get(
        "/api/v1/alerts/",
        params=params,
    )

    assert response.status_code == 422