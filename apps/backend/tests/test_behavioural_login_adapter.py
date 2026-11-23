
"""Integration tests for database-backed login behavioural features."""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_attempt import LoginAttempt
from app.services.behavioural_detection.login_adapter import (
    extract_login_behaviour,
    login_attempt_to_event,
)


BASE = datetime(2026, 11, 20, 12, 0, 0)


async def add_attempt(
    db: AsyncSession,
    *,
    seconds: int,
    email: str = "alice@example.com",
    successful: bool = True,
    ip: str = "192.0.2.1",
) -> LoginAttempt:
    """Insert a deterministic attempt without committing the transaction."""

    attempt = LoginAttempt(
        email=email,
        successful=successful,
        ip_address=ip,
        timestamp=BASE + timedelta(seconds=seconds),
    )

    db.add(attempt)
    await db.flush()

    return attempt


async def test_first_login_has_no_history(
    db_session: AsyncSession,
) -> None:
    current = await add_attempt(db_session, seconds=0)

    features = (
        await extract_login_behaviour(db_session, current)
    ).as_dict()

    assert features["source_events_5m"] == 0
    assert features["account_events_1h"] == 0
    assert features["device_available"] == 0


async def test_previous_failures_are_counted(
    db_session: AsyncSession,
) -> None:
    await add_attempt(
        db_session, seconds=0, successful=False
    )
    await add_attempt(
        db_session, seconds=10, successful=False
    )
    current = await add_attempt(
        db_session, seconds=20, successful=True
    )

    features = (
        await extract_login_behaviour(db_session, current)
    ).as_dict()

    assert features["source_events_5m"] == 2
    assert features["source_failures_5m"] == 2
    assert features["account_failures_1h"] == 2
    assert features["source_failure_ratio_5m"] == pytest.approx(1.0)


async def test_other_accounts_contribute_to_source_history(
    db_session: AsyncSession,
) -> None:
    await add_attempt(
        db_session, seconds=0, email="alice@example.com"
    )
    await add_attempt(
        db_session, seconds=10, email="bob@example.com"
    )
    current = await add_attempt(
        db_session, seconds=20, email="charlie@example.com"
    )

    features = (
        await extract_login_behaviour(db_session, current)
    ).as_dict()

    assert features["source_events_5m"] == 2
    assert features["source_distinct_users_1h"] == 2
    assert features["account_events_1h"] == 0


async def test_future_and_equal_timestamp_events_are_excluded(
    db_session: AsyncSession,
) -> None:
    current = await add_attempt(db_session, seconds=20)

    # Neither event is allowed into the current event's history.
    await add_attempt(db_session, seconds=20)
    await add_attempt(db_session, seconds=30)

    features = (
        await extract_login_behaviour(db_session, current)
    ).as_dict()

    assert features["source_events_5m"] == 0
    assert features["account_events_1h"] == 0


async def test_old_history_expires(
    db_session: AsyncSession,
) -> None:
    await add_attempt(db_session, seconds=0)
    current = await add_attempt(db_session, seconds=86400)

    features = (
        await extract_login_behaviour(db_session, current)
    ).as_dict()

    assert features["source_events_24h"] == 0
    assert features["account_history_available"] == 0


async def test_changed_ip_is_detected(
    db_session: AsyncSession,
) -> None:
    await add_attempt(
        db_session, seconds=0, ip="192.0.2.1"
    )
    current = await add_attempt(
        db_session, seconds=10, ip="192.0.2.2"
    )

    features = (
        await extract_login_behaviour(db_session, current)
    ).as_dict()

    assert features["account_new_ip"] == 1
    assert features["account_new_device"] == 0


def test_missing_ip_placeholder_is_not_treated_as_known_ip() -> None:
    attempt = LoginAttempt(
        email="ALICE@EXAMPLE.COM",
        successful=True,
        ip_address="0.0.0.0",
        timestamp=BASE,
    )

    event = login_attempt_to_event(attempt)

    assert event.user_id == "alice@example.com"
    assert event.ip_address is None
    assert event.device_id is None
