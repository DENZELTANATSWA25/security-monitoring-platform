"""Factory for constructing validated detection rules."""

from collections.abc import Mapping
from typing import Any

from app.schemas.detection_rule_parameters import (
    BruteForceParameters,
    EventBurstParameters,
    ImpossibleTravelParameters,
    SuspiciousLoginParameters,
)
from app.services.detection.base import DetectionRule
from app.services.detection.brute_force_rule import BruteForceRule
from app.services.detection.event_burst_rule import EventBurstRule
from app.services.detection.impossible_travel_rule import (
    ImpossibleTravelRule,
)
from app.services.detection.suspicious_login_rule import (
    SuspiciousLoginRule,
)


def build_detection_rule(
    rule_name: str,
    parameters: Mapping[str, Any] | None = None,
) -> DetectionRule:
    """
    Construct a detection rule from validated runtime parameters.

    Missing values use the parameter schema defaults. Unknown rules and
    invalid parameters fail rather than silently changing detection behaviour.
    """

    raw_parameters = dict(parameters or {})

    if rule_name == BruteForceRule.name:
        validated = BruteForceParameters.model_validate(
            raw_parameters,
        )

        return BruteForceRule(
            failed_attempts_threshold=(
                validated.failed_attempts_threshold
            ),
        )

    if rule_name == EventBurstRule.name:
        validated = EventBurstParameters.model_validate(
            raw_parameters,
        )

        return EventBurstRule(
            event_threshold=validated.event_threshold,
            window_minutes=validated.window_minutes,
        )

    if rule_name == SuspiciousLoginRule.name:
        SuspiciousLoginParameters.model_validate(
            raw_parameters,
        )

        return SuspiciousLoginRule()

    if rule_name == ImpossibleTravelRule.name:
        validated = ImpossibleTravelParameters.model_validate(
            raw_parameters,
        )

        return ImpossibleTravelRule(
            max_travel_speed_kmh=(
                validated.max_travel_speed_kmh
            ),
            min_distance_km=validated.min_distance_km,
        )

    raise ValueError(
        f"Unknown detection rule: {rule_name}"
    )