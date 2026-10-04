"""Unit tests for detection-rule construction and parameter validation."""

import pytest
from pydantic import ValidationError

from app.services.detection.brute_force_rule import BruteForceRule
from app.services.detection.event_burst_rule import EventBurstRule
from app.services.detection.factory import build_detection_rule
from app.services.detection.impossible_travel_rule import (
    ImpossibleTravelRule,
)
from app.services.detection.suspicious_login_rule import (
    SuspiciousLoginRule,
)


def test_build_brute_force_rule_with_parameters() -> None:
    rule = build_detection_rule(
        "BRUTE_FORCE_ATTACK",
        {
            "failed_attempts_threshold": 10,
        },
    )

    assert isinstance(rule, BruteForceRule)
    assert rule.failed_attempts_threshold == 10


def test_build_event_burst_rule_with_parameters() -> None:
    rule = build_detection_rule(
        "EVENT_BURST",
        {
            "event_threshold": 20,
            "window_minutes": 15,
        },
    )

    assert isinstance(rule, EventBurstRule)
    assert rule.event_threshold == 20
    assert rule.window_minutes == 15


def test_build_impossible_travel_rule_with_parameters() -> None:
    rule = build_detection_rule(
        "IMPOSSIBLE_TRAVEL",
        {
            "max_travel_speed_kmh": 1200.0,
            "min_distance_km": 150.0,
        },
    )

    assert isinstance(rule, ImpossibleTravelRule)
    assert rule.max_travel_speed_kmh == 1200.0
    assert rule.min_distance_km == 150.0


def test_build_suspicious_login_rule() -> None:
    rule = build_detection_rule(
        "SUSPICIOUS_LOGIN",
        {},
    )

    assert isinstance(rule, SuspiciousLoginRule)


def test_missing_parameters_use_defaults() -> None:
    brute_force_rule = build_detection_rule(
        "BRUTE_FORCE_ATTACK",
        {},
    )

    event_burst_rule = build_detection_rule(
        "EVENT_BURST",
        {},
    )

    impossible_travel_rule = build_detection_rule(
        "IMPOSSIBLE_TRAVEL",
        {},
    )

    assert brute_force_rule.failed_attempts_threshold == 5

    assert event_burst_rule.event_threshold == 5
    assert event_burst_rule.window_minutes == 5

    assert impossible_travel_rule.max_travel_speed_kmh == 1000.0
    assert impossible_travel_rule.min_distance_km == 100.0


def test_invalid_numeric_parameter_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_detection_rule(
            "BRUTE_FORCE_ATTACK",
            {
                "failed_attempts_threshold": 0,
            },
        )


def test_unknown_parameter_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_detection_rule(
            "EVENT_BURST",
            {
                "event_threshold": 5,
                "window_minutes": 5,
                "unknown_parameter": 123,
            },
        )


def test_parameters_not_supported_by_rule_are_rejected() -> None:
    with pytest.raises(ValidationError):
        build_detection_rule(
            "SUSPICIOUS_LOGIN",
            {
                "threshold": 5,
            },
        )


def test_unknown_rule_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Unknown detection rule",
    ):
        build_detection_rule(
            "NOT_A_REAL_RULE",
            {},
        )