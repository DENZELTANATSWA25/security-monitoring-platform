"""Integration tests for audit-log querying."""

from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


pytestmark = pytest.mark.asyncio


async def create_test_audit_log(
    db_session: AsyncSession,
    *,
    user_id: int | None,
    action: str,
    resource: str,
    details: str | None,
    timestamp: datetime,
) -> AuditLog:
    """Create an audit log with predictable query-test data."""

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
        timestamp=timestamp,
    )

    db_session.add(audit_log)
    await db_session.commit()
    await db_session.refresh(audit_log)

    return audit_log


async def test_audit_logs_are_paginated(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    base_time = datetime(2026, 10, 1, 12, 0, 0)

    for index in range(3):
        await create_test_audit_log(
            db_session,
            user_id=None,
            action=f"PAGINATION_ACTION_{index}",
            resource="QUERY_TEST",
            details=f"Pagination audit test {index}",
            timestamp=base_time + timedelta(minutes=index),
        )

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "resource": "QUERY_TEST",
            "limit": 2,
            "offset": 1,
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) == 2
    assert logs[0]["action"] == "PAGINATION_ACTION_1"
    assert logs[1]["action"] == "PAGINATION_ACTION_2"


async def test_audit_logs_can_be_filtered_by_user_id(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    admin_user,
    analyst_user,
) -> None:
    now = datetime(2026, 10, 2, 12, 0, 0)

    await create_test_audit_log(
        db_session,
        user_id=admin_user.id,
        action="ADMIN_QUERY_ACTION",
        resource="USER_FILTER_TEST",
        details="Admin audit action",
        timestamp=now,
    )

    await create_test_audit_log(
        db_session,
        user_id=analyst_user.id,
        action="ANALYST_QUERY_ACTION",
        resource="USER_FILTER_TEST",
        details="Analyst audit action",
        timestamp=now + timedelta(minutes=1),
    )

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "user_id": admin_user.id,
            "resource": "USER_FILTER_TEST",
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) == 1
    assert logs[0]["user_id"] == admin_user.id
    assert logs[0]["action"] == "ADMIN_QUERY_ACTION"


async def test_audit_logs_can_be_filtered_by_action(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(2026, 10, 3, 12, 0, 0)

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="ROLE_CHANGED_QUERY_TEST",
        resource="ACTION_FILTER_TEST",
        details="Role changed",
        timestamp=now,
    )

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="STATUS_CHANGED_QUERY_TEST",
        resource="ACTION_FILTER_TEST",
        details="Status changed",
        timestamp=now + timedelta(minutes=1),
    )

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "action": "ROLE_CHANGED_QUERY_TEST",
            "resource": "ACTION_FILTER_TEST",
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) == 1
    assert logs[0]["action"] == "ROLE_CHANGED_QUERY_TEST"


async def test_audit_logs_can_be_filtered_by_resource(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    now = datetime(2026, 10, 4, 12, 0, 0)

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="RESOURCE_QUERY_ACTION",
        resource="USER",
        details="User resource audit",
        timestamp=now,
    )

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="RESOURCE_QUERY_ACTION",
        resource="TELEMETRY_SOURCE",
        details="Telemetry resource audit",
        timestamp=now + timedelta(minutes=1),
    )

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "resource": "TELEMETRY_SOURCE",
            "action": "RESOURCE_QUERY_ACTION",
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) == 1
    assert logs[0]["resource"] == "TELEMETRY_SOURCE"


@pytest.mark.parametrize(
    ("search", "expected_action"),
    [
        ("SEARCH_ACTION_TOKEN", "SEARCH_ACTION_TOKEN"),
        ("SEARCH_RESOURCE_TOKEN", "RESOURCE_SEARCH_ACTION"),
        ("credential rotation", "DETAILS_SEARCH_ACTION"),
    ],
)
async def test_audit_logs_can_be_searched_across_text_fields(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    search: str,
    expected_action: str,
) -> None:
    now = datetime(2026, 10, 5, 12, 0, 0)

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="SEARCH_ACTION_TOKEN",
        resource="SEARCH_TEST_ONE",
        details="First searchable audit record",
        timestamp=now,
    )

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="RESOURCE_SEARCH_ACTION",
        resource="SEARCH_RESOURCE_TOKEN",
        details="Second searchable audit record",
        timestamp=now + timedelta(minutes=1),
    )

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="DETAILS_SEARCH_ACTION",
        resource="SEARCH_TEST_THREE",
        details="Telemetry credential rotation completed",
        timestamp=now + timedelta(minutes=2),
    )

    response = await admin_client.get(
        "/api/v1/audit",
        params={"search": search},
    )

    assert response.status_code == 200

    actions = {
        log["action"]
        for log in response.json()
    }

    assert expected_action in actions


async def test_audit_search_is_case_insensitive(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_test_audit_log(
        db_session,
        user_id=None,
        action="CASE_INSENSITIVE_AUDIT",
        resource="SEARCH_CASE_TEST",
        details="Suspicious Administrative Activity",
        timestamp=datetime(2026, 10, 5, 15, 0, 0),
    )

    response = await admin_client.get(
        "/api/v1/audit",
        params={"search": "administrative activity"},
    )

    assert response.status_code == 200

    actions = {
        log["action"]
        for log in response.json()
    }

    assert "CASE_INSENSITIVE_AUDIT" in actions


async def test_audit_logs_can_be_filtered_by_date_range(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    await create_test_audit_log(
        db_session,
        user_id=None,
        action="AUDIT_BEFORE_RANGE",
        resource="DATE_RANGE_TEST",
        details="Date range audit test",
        timestamp=datetime(2026, 9, 30, 12, 0, 0),
    )

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="AUDIT_INSIDE_RANGE",
        resource="DATE_RANGE_TEST",
        details="Date range audit test",
        timestamp=datetime(2026, 10, 3, 12, 0, 0),
    )

    await create_test_audit_log(
        db_session,
        user_id=None,
        action="AUDIT_AFTER_RANGE",
        resource="DATE_RANGE_TEST",
        details="Date range audit test",
        timestamp=datetime(2026, 10, 8, 12, 0, 0),
    )

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "resource": "DATE_RANGE_TEST",
            "start_date": "2026-10-01T00:00:00",
            "end_date": "2026-10-07T23:59:59",
        },
    )

    assert response.status_code == 200

    logs = response.json()

    assert len(logs) == 1
    assert logs[0]["action"] == "AUDIT_INSIDE_RANGE"


async def test_audit_logs_support_ascending_and_descending_order(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    base_time = datetime(2026, 10, 6, 12, 0, 0)

    for index in range(3):
        await create_test_audit_log(
            db_session,
            user_id=None,
            action=f"ORDER_AUDIT_{index}",
            resource="ORDERING_TEST",
            details=f"Ordering audit {index}",
            timestamp=base_time + timedelta(minutes=index),
        )

    ascending = await admin_client.get(
        "/api/v1/audit",
        params={
            "resource": "ORDERING_TEST",
            "sort_order": "asc",
        },
    )

    descending = await admin_client.get(
        "/api/v1/audit",
        params={
            "resource": "ORDERING_TEST",
            "sort_order": "desc",
        },
    )

    assert ascending.status_code == 200
    assert descending.status_code == 200

    assert [
        log["action"]
        for log in ascending.json()
    ] == [
        "ORDER_AUDIT_0",
        "ORDER_AUDIT_1",
        "ORDER_AUDIT_2",
    ]

    assert [
        log["action"]
        for log in descending.json()
    ] == [
        "ORDER_AUDIT_2",
        "ORDER_AUDIT_1",
        "ORDER_AUDIT_0",
    ]


async def test_non_admin_cannot_query_audit_logs(
    viewer_client: AsyncClient,
) -> None:
    response = await viewer_client.get(
        "/api/v1/audit",
        params={
            "search": "anything",
            "limit": 10,
        },
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
        {"user_id": 0},
        {"action": ""},
        {"resource": ""},
        {"search": ""},
        {"sort_order": "random"},
    ],
)
async def test_invalid_audit_query_parameters_are_rejected(
    admin_client: AsyncClient,
    params: dict,
) -> None:
    response = await admin_client.get(
        "/api/v1/audit",
        params=params,
    )

    assert response.status_code == 422