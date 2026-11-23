
"""Parity tests for optimised behavioural history reconstruction."""

from datetime import datetime, timedelta

from app.models.login_attempt import LoginAttempt
from app.services.behavioural_detection.features import (
    BehaviourFeatureExtractorV2,
)
from app.services.behavioural_detection.login_adapter import (
    build_extractor_from_history,
    login_attempt_to_event,
)


def make_attempt(index: int, base: datetime) -> LoginAttempt:
    """Create deterministic synthetic login history."""

    return LoginAttempt(
        id=index + 1,
        email=f"user-{index % 17}@example.invalid",
        successful=index % 4 != 0,
        ip_address=f"192.0.2.{index % 200 + 1}",
        timestamp=base + timedelta(seconds=index * 10),
    )


def test_optimised_history_matches_frozen_replay() -> None:
    """Both paths must produce identical 22-feature vectors."""

    base = datetime(2026, 11, 20, 12, 0, 0)

    history = [
        make_attempt(i, base)
        for i in range(1000)
    ]

    current = make_attempt(1000, base)

    # Reference: original frozen chronological replay.
    reference = BehaviourFeatureExtractorV2()

    for previous in history:
        reference.transform_one(
            login_attempt_to_event(previous)
        )

    expected = reference.transform_one(
        login_attempt_to_event(current)
    )

    # Optimised: load history state directly.
    optimised = build_extractor_from_history(history)

    actual = optimised.transform_one(
        login_attempt_to_event(current)
    )

    assert actual.values == expected.values
    assert len(actual.values) == 22


def test_optimised_history_handles_empty_history() -> None:
    """First-time logins must preserve baseline behaviour."""

    current = LoginAttempt(
        id=1,
        email="first@example.invalid",
        successful=True,
        ip_address="192.0.2.1",
        timestamp=datetime(2026, 11, 20, 12, 0, 0),
    )

    reference = BehaviourFeatureExtractorV2()
    expected = reference.transform_one(
        login_attempt_to_event(current)
    )

    optimised = build_extractor_from_history([])
    actual = optimised.transform_one(
        login_attempt_to_event(current)
    )

    assert actual.values == expected.values


import pytest

from app.services.behavioural_detection.login_adapter import (
    BehaviouralFeatureError,
)


def assert_history_parity(history, current):
    """Compare optimised reconstruction with frozen replay."""

    reference = BehaviourFeatureExtractorV2()

    for attempt in history:
        reference.transform_one(
            login_attempt_to_event(attempt)
        )

    expected = reference.transform_one(
        login_attempt_to_event(current)
    )

    optimised = build_extractor_from_history(history)

    actual = optimised.transform_one(
        login_attempt_to_event(current)
    )

    assert actual.values == expected.values


def test_parity_across_window_boundaries():
    """Exercise 5-minute, 1-hour and 24-hour boundaries."""

    now = datetime(2026, 11, 20, 12, 0, 0)

    offsets = [
        86400, 86399, 3600, 3599,
        300, 299, 60, 1,
    ]

    history = [
        LoginAttempt(
            id=index + 1,
            email="boundary@example.invalid",
            successful=index % 2 == 0,
            ip_address="192.0.2.1",
            timestamp=now - timedelta(seconds=offset),
        )
        for index, offset in enumerate(offsets)
    ]

    history.sort(key=lambda item: (item.timestamp, item.id))

    current = LoginAttempt(
        id=100,
        email="boundary@example.invalid",
        successful=False,
        ip_address="192.0.2.2",
        timestamp=now,
    )

    assert_history_parity(history, current)


def test_parity_with_multiple_accounts_and_ips():
    """Preserve source-wide and account-specific statistics."""

    now = datetime(2026, 11, 20, 12, 0, 0)

    history = [
        LoginAttempt(
            id=index + 1,
            email=f"user-{index % 4}@example.invalid",
            successful=index % 3 != 0,
            ip_address=(
                "192.0.2.1"
                if index % 2 == 0
                else "192.0.2.2"
            ),
            timestamp=now - timedelta(minutes=100 - index),
        )
        for index in range(100)
    ]

    current = LoginAttempt(
        id=101,
        email="user-0@example.invalid",
        successful=False,
        ip_address="203.0.113.10",
        timestamp=now,
    )

    assert_history_parity(history, current)


def test_parity_with_invalid_and_missing_ips():
    """Invalid IPs must be normalised identically."""

    now = datetime(2026, 11, 20, 12, 0, 0)

    addresses = [
        "192.0.2.1",
        " 192.0.2.1 ",
        "invalid-ip",
        "0.0.0.0",
        "2001:0db8::1",
        "2001:db8::1",
    ]

    history = [
        LoginAttempt(
            id=index + 1,
            email="ip-test@example.invalid",
            successful=True,
            ip_address=address,
            timestamp=now - timedelta(
                minutes=len(addresses) - index
            ),
        )
        for index, address in enumerate(addresses)
    ]

    current = LoginAttempt(
        id=100,
        email="ip-test@example.invalid",
        successful=False,
        ip_address="203.0.113.10",
        timestamp=now,
    )

    assert_history_parity(history, current)


def test_out_of_order_history_is_rejected():
    """The loader must reject reversed timestamps."""

    now = datetime(2026, 11, 20, 12, 0, 0)

    history = [
        LoginAttempt(
            id=1,
            email="test@example.invalid",
            successful=True,
            ip_address="192.0.2.1",
            timestamp=now,
        ),
        LoginAttempt(
            id=2,
            email="test@example.invalid",
            successful=False,
            ip_address="192.0.2.2",
            timestamp=now - timedelta(minutes=1),
        ),
    ]

    with pytest.raises(BehaviouralFeatureError):
        build_extractor_from_history(history)
