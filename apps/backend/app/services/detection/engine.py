"""Orchestrates execution of security detection rules."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.detection.base import DetectionContext
from app.services.detection.brute_force_rule import BruteForceRule
from app.services.detection.event_burst_rule import EventBurstRule
from app.services.detection.factory import build_detection_rule
from app.services.detection.impossible_travel_rule import (
    ImpossibleTravelRule,
)
from app.services.detection.result import DetectionResult
from app.services.detection.suspicious_login_rule import (
    SuspiciousLoginRule,
)
from app.services.detection_rule_config_service import (
    get_detection_rule_config_by_name,
)


rule_names = [
    BruteForceRule.name,
    EventBurstRule.name,
    SuspiciousLoginRule.name,
    ImpossibleTravelRule.name,
]


async def run_detection(
    db: AsyncSession,
    context: DetectionContext,
) -> list[DetectionResult]:
    """Run operationally enabled detection rules against the context."""

    triggered_results: list[DetectionResult] = []

    for rule_name in rule_names:
        config = await get_detection_rule_config_by_name(
            db=db,
            rule_name=rule_name,
        )

        # Preserve the existing behaviour for Python rules that have not yet
        # received persisted configuration.
        if config is None:
            rule = build_detection_rule(
                rule_name,
            )
        else:
            if not config.is_enabled:
                continue

            rule = build_detection_rule(
                rule_name,
                config.parameters,
            )

        result = await rule.evaluate(
            db,
            context,
        )

        if result.triggered:
            triggered_results.append(result)

    return triggered_results