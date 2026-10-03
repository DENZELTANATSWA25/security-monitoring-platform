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
from app.services.detection.suspicious_login_rule import SuspiciousLoginRule
from app.services.detection.geo import haversine_distance_km
from app.services.detection.impossible_travel_rule import (
    ImpossibleTravelRule,
)


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

def test_haversine_distance_is_zero_for_same_location() -> None:
    """Identical coordinates should have zero geographic distance."""

    distance = haversine_distance_km(
        51.5074,
        -0.1278,
        51.5074,
        -0.1278,
    )

    assert distance == pytest.approx(0.0)


def test_haversine_distance_between_london_and_new_york() -> None:
    """London and New York should be roughly 5,570 km apart."""

    distance = haversine_distance_km(
        51.5074,
        -0.1278,
        40.7128,
        -74.0060,
    )

    assert distance == pytest.approx(
        5570,
        abs=20,
    )


async def test_engine_ignores_non_triggered_rules(
    db_session: AsyncSession,
) -> None:
    """Rules that do not trigger should not appear in engine output."""

    rule = AsyncMock()
    rule.name = "TEST_NON_TRIGGERED_RULE"
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
    rule.name = "TEST_TRIGGERED_RULE"
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
    first_rule.name = "FIRST_TEST_RULE"
    first_rule.evaluate.return_value = first_detection

    ignored_rule = AsyncMock()
    ignored_rule.name = "IGNORED_TEST_RULE"
    ignored_rule.evaluate.return_value = DetectionResult.not_triggered()

    second_rule = AsyncMock()
    second_rule.name = "SECOND_TEST_RULE"
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
    rule.name = "FAILING_TEST_RULE"
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

async def test_suspicious_login_rule_ignores_missing_login_attempt(
    db_session: AsyncSession,
) -> None:
    """Suspicious-login detection requires a login attempt."""

    result = await SuspiciousLoginRule().evaluate(
        db_session,
        DetectionContext(),
    )

    assert result == DetectionResult.not_triggered()


async def test_suspicious_login_rule_ignores_failed_login(
    db_session: AsyncSession,
) -> None:
    """Failed logins should not be evaluated as suspicious successful logins."""

    attempt = LoginAttempt(
        email="failed-suspicious@example.com",
        successful=False,
        ip_address="192.0.2.200",
    )

    db_session.add(attempt)
    await db_session.flush()

    result = await SuspiciousLoginRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()


async def test_suspicious_login_rule_first_success_establishes_baseline(
    db_session: AsyncSession,
) -> None:
    """The first successful login should establish IP history without alerting."""

    attempt = LoginAttempt(
        email="first-success@example.com",
        successful=True,
        ip_address="192.0.2.201",
    )

    db_session.add(attempt)
    await db_session.flush()

    result = await SuspiciousLoginRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()


async def test_suspicious_login_rule_ignores_known_ip(
    db_session: AsyncSession,
) -> None:
    """A successful login from previously observed IP history should not alert."""

    email = "known-rule-ip@example.com"
    ip_address = "192.0.2.202"

    previous_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address=ip_address,
    )

    db_session.add(previous_attempt)
    await db_session.flush()

    current_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address=ip_address,
    )

    db_session.add(current_attempt)
    await db_session.flush()

    result = await SuspiciousLoginRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=current_attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()


async def test_suspicious_login_rule_triggers_for_new_ip(
    db_session: AsyncSession,
) -> None:
    """A successful login from an unseen IP should trigger after history exists."""

    email = "new-rule-ip@example.com"

    previous_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="192.0.2.203",
    )

    db_session.add(previous_attempt)
    await db_session.flush()

    current_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="203.0.113.203",
    )

    db_session.add(current_attempt)
    await db_session.flush()

    result = await SuspiciousLoginRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=current_attempt,
        ),
    )

    assert result.triggered is True
    assert result.alert_type == "SUSPICIOUS_LOGIN"
    assert result.severity == "MEDIUM"
    assert result.message is not None
    assert email in result.message
    assert current_attempt.ip_address in result.message


async def test_impossible_travel_rule_ignores_missing_login_attempt(
    db_session: AsyncSession,
) -> None:
    """Impossible-travel detection requires a login attempt."""

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(),
    )

    assert result == DetectionResult.not_triggered()


async def test_impossible_travel_rule_ignores_failed_login(
    db_session: AsyncSession,
) -> None:
    """Failed authentication attempts should not run travel detection."""

    attempt = LoginAttempt(
        email="travel-failed@example.com",
        successful=False,
        ip_address="192.0.2.200",
        latitude=51.5074,
        longitude=-0.1278,
        timestamp=datetime.utcnow(),
    )

    db_session.add(attempt)
    await db_session.flush()

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()


async def test_impossible_travel_rule_ignores_missing_location(
    db_session: AsyncSession,
) -> None:
    """A successful login without coordinates cannot be compared geographically."""

    attempt = LoginAttempt(
        email="travel-no-location@example.com",
        successful=True,
        ip_address="192.0.2.201",
        latitude=None,
        longitude=None,
        timestamp=datetime.utcnow(),
    )

    db_session.add(attempt)
    await db_session.flush()

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()


async def test_impossible_travel_rule_first_location_establishes_baseline(
    db_session: AsyncSession,
) -> None:
    """The first geolocated successful login should establish a baseline."""

    attempt = LoginAttempt(
        email="travel-baseline@example.com",
        successful=True,
        ip_address="192.0.2.202",
        latitude=51.5074,
        longitude=-0.1278,
        timestamp=datetime.utcnow(),
    )

    db_session.add(attempt)
    await db_session.flush()

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()


async def test_impossible_travel_rule_allows_realistic_travel(
    db_session: AsyncSession,
) -> None:
    """A long-distance login after enough travel time should not trigger."""

    email = "travel-realistic@example.com"
    current_time = datetime.utcnow()

    previous_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="192.0.2.203",
        latitude=51.5074,
        longitude=-0.1278,
        timestamp=current_time - timedelta(hours=10),
    )

    current_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="203.0.113.203",
        latitude=40.7128,
        longitude=-74.0060,
        timestamp=current_time,
    )

    db_session.add_all([
        previous_attempt,
        current_attempt,
    ])
    await db_session.flush()

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=current_attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()


async def test_impossible_travel_rule_triggers_for_unrealistic_travel(
    db_session: AsyncSession,
) -> None:
    """London to New York in one hour should trigger impossible travel."""

    email = "travel-impossible@example.com"
    current_time = datetime.utcnow()

    previous_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="192.0.2.204",
        latitude=51.5074,
        longitude=-0.1278,
        timestamp=current_time - timedelta(hours=1),
    )

    current_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="203.0.113.204",
        latitude=40.7128,
        longitude=-74.0060,
        timestamp=current_time,
    )

    db_session.add_all([
        previous_attempt,
        current_attempt,
    ])
    await db_session.flush()

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=current_attempt,
        ),
    )

    assert result.triggered is True
    assert result.alert_type == "IMPOSSIBLE_TRAVEL"
    assert result.severity == "HIGH"
    assert result.message is not None
    assert email in result.message

async def test_impossible_travel_rule_allows_nearby_locations(
    db_session: AsyncSession,
) -> None:
    """Nearby successful logins should not be classified as impossible travel."""

    email = "travel-nearby@example.com"
    current_time = datetime.utcnow()

    previous_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="192.0.2.210",
        latitude=51.5074,
        longitude=-0.1278,
        timestamp=current_time - timedelta(minutes=10),
    )

    current_attempt = LoginAttempt(
        email=email,
        successful=True,
        ip_address="203.0.113.210",
        latitude=51.5155,
        longitude=-0.0922,
        timestamp=current_time,
    )

    db_session.add_all([
        previous_attempt,
        current_attempt,
    ])
    await db_session.flush()

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=current_attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()

async def test_impossible_travel_history_is_isolated_by_account(
    db_session: AsyncSession,
) -> None:
    """Another account's location history must not affect this account."""

    current_time = datetime.utcnow()

    other_account_attempt = LoginAttempt(
        email="other-traveller@example.com",
        successful=True,
        ip_address="192.0.2.211",
        latitude=51.5074,
        longitude=-0.1278,
        timestamp=current_time - timedelta(minutes=30),
    )

    target_attempt = LoginAttempt(
        email="target-traveller@example.com",
        successful=True,
        ip_address="203.0.113.211",
        latitude=40.7128,
        longitude=-74.0060,
        timestamp=current_time,
    )

    db_session.add_all([
        other_account_attempt,
        target_attempt,
    ])
    await db_session.flush()

    result = await ImpossibleTravelRule().evaluate(
        db_session,
        DetectionContext(
            login_attempt=target_attempt,
        ),
    )

    assert result == DetectionResult.not_triggered()

async def test_engine_executes_enabled_configured_rule(
    db_session: AsyncSession,
) -> None:
    """A rule with enabled persisted configuration should execute."""

    from app.models.detection_rule_config import DetectionRuleConfig

    config = DetectionRuleConfig(
        rule_name="CONFIGURED_ENABLED_RULE",
        display_name="Configured Enabled Rule",
        description="Enabled rule used by the engine integration test.",
        is_enabled=True,
    )

    db_session.add(config)
    await db_session.flush()

    rule = AsyncMock()
    rule.name = "CONFIGURED_ENABLED_RULE"
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


async def test_engine_skips_disabled_configured_rule(
    db_session: AsyncSession,
) -> None:
    """A disabled persisted rule must not be evaluated."""

    from app.models.detection_rule_config import DetectionRuleConfig

    config = DetectionRuleConfig(
        rule_name="CONFIGURED_DISABLED_RULE",
        display_name="Configured Disabled Rule",
        description="Disabled rule used by the engine integration test.",
        is_enabled=False,
    )

    db_session.add(config)
    await db_session.flush()

    rule = AsyncMock()
    rule.name = "CONFIGURED_DISABLED_RULE"

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
    rule.evaluate.assert_not_awaited()


async def test_engine_executes_unconfigured_rule_by_default(
    db_session: AsyncSession,
) -> None:
    """Rules without persisted configuration should remain enabled."""

    rule = AsyncMock()
    rule.name = "UNCONFIGURED_ENGINE_TEST_RULE"
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


async def test_engine_only_executes_operationally_enabled_rules(
    db_session: AsyncSession,
) -> None:
    """Mixed rule configuration should execute only operational rules."""

    from app.models.detection_rule_config import DetectionRuleConfig

    enabled_config = DetectionRuleConfig(
        rule_name="MIXED_ENABLED_RULE",
        display_name="Mixed Enabled Rule",
        description="Enabled rule in a mixed engine test.",
        is_enabled=True,
    )

    disabled_config = DetectionRuleConfig(
        rule_name="MIXED_DISABLED_RULE",
        display_name="Mixed Disabled Rule",
        description="Disabled rule in a mixed engine test.",
        is_enabled=False,
    )

    db_session.add_all([
        enabled_config,
        disabled_config,
    ])
    await db_session.flush()

    enabled_detection = DetectionResult.triggered_alert(
        alert_type="MIXED_ENABLED_ALERT",
        severity="HIGH",
        message="Enabled configured rule triggered.",
    )

    enabled_rule = AsyncMock()
    enabled_rule.name = "MIXED_ENABLED_RULE"
    enabled_rule.evaluate.return_value = enabled_detection

    disabled_rule = AsyncMock()
    disabled_rule.name = "MIXED_DISABLED_RULE"

    unconfigured_rule = AsyncMock()
    unconfigured_rule.name = "MIXED_UNCONFIGURED_RULE"
    unconfigured_rule.evaluate.return_value = (
        DetectionResult.not_triggered()
    )

    context = DetectionContext()

    with patch(
        "app.services.detection.engine.rules",
        [
            enabled_rule,
            disabled_rule,
            unconfigured_rule,
        ],
    ):
        results = await run_detection(
            db_session,
            context,
        )

    assert results == [enabled_detection]

    enabled_rule.evaluate.assert_awaited_once_with(
        db_session,
        context,
    )

    disabled_rule.evaluate.assert_not_awaited()

    unconfigured_rule.evaluate.assert_awaited_once_with(
        db_session,
        context,
    )