"""Unit tests for the reusable security detection framework."""

from dataclasses import FrozenInstanceError
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.detection.brute_force_rule import BruteForceRule
from app.services.detection.engine import run_detection
from app.services.detection.result import DetectionResult
from app.models.security_event import (
    SecurityEvent,
    EventSeverity,
)
from app.services.detection.event_burst_rule import EventBurstRule

from app.models.login_attempt import LoginAttempt
from app.services.detection.base import DetectionContext


def test_not_triggered_result_has_no_alert_data() -> None:
    """A non-triggered result should contain no alert information."""

    result = DetectionResult.not_triggered()

    assert result.triggered is False
    assert result.alert_type is None
    assert result.severity is None
    assert result.message is None


def test_triggered_result_contains_alert_data() -> None:
    """A triggered result should retain the alert information."""

    result = DetectionResult.triggered_alert(
        alert_type="TEST_DETECTION",
        severity="HIGH",
        message="Synthetic security detection.",
    )

    assert result.triggered is True
    assert result.alert_type == "TEST_DETECTION"
    assert result.severity == "HIGH"
    assert result.message == "Synthetic security detection."


def test_detection_result_is_immutable() -> None:
    """Detection results should not be mutable after creation."""

    result = DetectionResult.not_triggered()

    with pytest.raises(FrozenInstanceError):
        result.triggered = True


async def test_engine_ignores_non_triggered_rules(
    db_session: AsyncSession,
) -> None:
    """Rules that do not trigger should not appear in engine output."""

    rule = AsyncMock()
    rule.evaluate.return_value = DetectionResult.not_triggered()
    context = DetectionContext()

    with patch(
        "app.services.detection.engine.rules",
        [rule],
    ):
        results = await run_detection(
            db_session,
            context,
        )

    assert results == []
    rule.evaluate.assert_awaited_once_with(
        db_session,
        context,
    )


async def test_engine_collects_triggered_results(
    db_session: AsyncSession,
) -> None:
    """Triggered detections should be returned by the engine."""

    detection = DetectionResult.triggered_alert(
        alert_type="TEST_ALERT",
        severity="HIGH",
        message="Test detection triggered.",
    )
    context = DetectionContext()

    rule = AsyncMock()
    rule.evaluate.return_value = detection

    with patch(
        "app.services.detection.engine.rules",
        [rule],
    ):
        results = await run_detection(
            db_session,
            context,
        )

    assert results == [detection]


async def test_engine_collects_multiple_triggered_results(
    db_session: AsyncSession,
) -> None:
    """The engine should retain detections from multiple triggered rules."""

    first_detection = DetectionResult.triggered_alert(
        alert_type="FIRST_TEST_ALERT",
        severity="HIGH",
        message="First rule triggered.",
    )

    second_detection = DetectionResult.triggered_alert(
        alert_type="SECOND_TEST_ALERT",
        severity="CRITICAL",
        message="Second rule triggered.",
    )

    first_rule = AsyncMock()
    first_rule.evaluate.return_value = first_detection

    ignored_rule = AsyncMock()
    ignored_rule.evaluate.return_value = DetectionResult.not_triggered()

    second_rule = AsyncMock()
    second_rule.evaluate.return_value = second_detection
    context = DetectionContext()

    with patch(
        "app.services.detection.engine.rules",
        [
            first_rule,
            ignored_rule,
            second_rule,
        ],
    ):
        results = await run_detection(
            db_session,
            context,
        )

    assert results == [
        first_detection,
        second_detection,
    ]


async def test_engine_propagates_rule_failure(
    db_session: AsyncSession,
) -> None:
    """
    Detection failures should propagate to the owning transaction.

    Event and login-attempt services are responsible for rolling back their
    database transactions when detection fails.
    """
    context = DetectionContext()

    rule = AsyncMock()
    rule.evaluate.side_effect = RuntimeError(
        "Synthetic detection failure"
    )

    with patch(
        "app.services.detection.engine.rules",
        [rule],
    ):
        with pytest.raises(
            RuntimeError,
            match="Synthetic detection failure",
        ):
            await run_detection(
                db_session,
                context,
            )


async def test_brute_force_rule_ignores_missing_login_attempt(
    db_session: AsyncSession,
) -> None:
    """Brute-force detection requires an account identifier."""

    rule = BruteForceRule()

    with patch(
        "app.services.detection.brute_force_rule.count_failed_attempts",
        new=AsyncMock(),
    ) as count_mock:
        result = await rule.evaluate(
            db_session,
            DetectionContext(),
        )

    assert result == DetectionResult.not_triggered()
    count_mock.assert_not_awaited()


async def test_brute_force_rule_does_not_trigger_below_threshold(
    db_session: AsyncSession,
) -> None:
    """Fewer than five recent failures should not trigger an alert."""

    attempt = LoginAttempt(
        email="user@example.com",
        successful=False,
        ip_address="192.0.2.10",
    )

    rule = BruteForceRule()

    with patch(
        "app.services.detection.brute_force_rule.count_failed_attempts",
        new=AsyncMock(return_value=4),
    ) as count_mock:
        result = await rule.evaluate(
            db_session,
            DetectionContext(
                login_attempt=attempt,
            ),
        )

    assert result == DetectionResult.not_triggered()

    count_mock.assert_awaited_once_with(
        db_session,
        "user@example.com",
    )


async def test_brute_force_rule_triggers_at_threshold(
    db_session: AsyncSession,
) -> None:
    """Five recent failures should trigger brute-force detection."""

    attempt = LoginAttempt(
        email="user@example.com",
        successful=False,
        ip_address="192.0.2.10",
    )

    rule = BruteForceRule()

    with patch(
        "app.services.detection.brute_force_rule.count_failed_attempts",
        new=AsyncMock(return_value=5),
    ) as count_mock:
        result = await rule.evaluate(
            db_session,
            DetectionContext(
                login_attempt=attempt,
            ),
        )

    assert result == DetectionResult.triggered_alert(
        alert_type="BRUTE_FORCE_ATTACK",
        severity="CRITICAL",
        message="Brute force attack detected on user@example.com",
    )

    count_mock.assert_awaited_once_with(
        db_session,
        "user@example.com",
    )

async def test_event_burst_rule_ignores_missing_event(
    db_session: AsyncSession,
) -> None:
    """Event burst detection should ignore non-event contexts."""

    rule = EventBurstRule()

    result = await rule.evaluate(
        db_session,
        DetectionContext(),
    )

    assert result.triggered is False
    assert result.alert_type is None
    assert result.severity is None
    assert result.message is None


async def test_event_burst_rule_does_not_trigger_below_threshold(
    db_session,
) -> None:
    """Fewer than five recent events from one source should not trigger."""

    source = "burst-test-below-threshold"
    reference_time = datetime.utcnow()

    events = [
        SecurityEvent(
            event_type=f"BURST_TEST_{index}",
            severity=EventSeverity.INFO,
            source=source,
            message=f"Test event {index}",
            created_at=reference_time - timedelta(seconds=index),
        )
        for index in range(4)
    ]

    db_session.add_all(events)
    await db_session.flush()

    current_event = events[0]

    result = await EventBurstRule().evaluate(
        db_session,
        DetectionContext(
            event=current_event,
        ),
    )

    assert result.triggered is False

async def test_event_burst_rule_triggers_at_threshold(
    db_session,
) -> None:
    """Five recent events from one source should trigger burst detection."""

    source = "burst-test-at-threshold"
    reference_time = datetime.utcnow()

    events = [
        SecurityEvent(
            event_type=f"BURST_TEST_{index}",
            severity=EventSeverity.WARNING,
            source=source,
            message=f"Test event {index}",
            created_at=reference_time - timedelta(seconds=index),
        )
        for index in range(5)
    ]

    db_session.add_all(events)
    await db_session.flush()

    current_event = events[0]

    result = await EventBurstRule().evaluate(
        db_session,
        DetectionContext(
            event=current_event,
        ),
    )

    assert result.triggered is True
    assert result.alert_type == "EVENT_BURST"
    assert result.severity == "HIGH"
    assert result.message is not None
    assert source in result.message


async def test_event_burst_rule_ignores_events_outside_window(
    db_session,
) -> None:
    """Old events should not contribute to the five-minute threshold."""

    source = "burst-test-old-events"
    reference_time = datetime.utcnow()

    recent_events = [
        SecurityEvent(
            event_type=f"RECENT_BURST_TEST_{index}",
            severity=EventSeverity.INFO,
            source=source,
            message=f"Recent test event {index}",
            created_at=reference_time - timedelta(seconds=index),
        )
        for index in range(4)
    ]

    old_event = SecurityEvent(
        event_type="OLD_BURST_TEST",
        severity=EventSeverity.INFO,
        source=source,
        message="Old event outside detection window",
        created_at=reference_time - timedelta(minutes=10),
    )

    db_session.add_all(
        [
            *recent_events,
            old_event,
        ]
    )
    await db_session.flush()

    result = await EventBurstRule().evaluate(
        db_session,
        DetectionContext(
            event=recent_events[0],
        ),
    )

    assert result.triggered is False


async def test_event_burst_rule_only_counts_same_source(
    db_session,
) -> None:
    """Events from different sources must not be combined."""

    reference_time = datetime.utcnow()

    primary_event = SecurityEvent(
        event_type="PRIMARY_SOURCE_EVENT",
        severity=EventSeverity.INFO,
        source="primary-source",
        message="Primary source event",
        created_at=reference_time,
    )

    other_events = [
        SecurityEvent(
            event_type=f"OTHER_SOURCE_EVENT_{index}",
            severity=EventSeverity.INFO,
            source="different-source",
            message=f"Different source event {index}",
            created_at=reference_time - timedelta(seconds=index),
        )
        for index in range(4)
    ]

    db_session.add_all(
        [
            primary_event,
            *other_events,
        ]
    )
    await db_session.flush()

    result = await EventBurstRule().evaluate(
        db_session,
        DetectionContext(
            event=primary_event,
        ),
    )

    assert result.triggered is False

async def test_brute_force_rule_ignores_successful_login(
    db_session: AsyncSession,
) -> None:
    """Successful authentication attempts should not run brute-force detection."""

    attempt = LoginAttempt(
        email="user@example.com",
        successful=True,
        ip_address="192.0.2.10",
    )

    rule = BruteForceRule()

    with patch(
        "app.services.detection.brute_force_rule.count_failed_attempts",
        new=AsyncMock(),
    ) as count_mock:
        result = await rule.evaluate(
            db_session,
            DetectionContext(
                login_attempt=attempt,
            ),
        )

    assert result == DetectionResult.not_triggered()
    count_mock.assert_not_awaited()