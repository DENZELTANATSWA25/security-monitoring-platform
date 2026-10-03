"""Orchestrates execution of security detection rules."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.detection.base import DetectionContext
from app.services.detection.brute_force_rule import BruteForceRule
from app.services.detection.event_burst_rule import EventBurstRule
from app.services.detection.impossible_travel_rule import (
    ImpossibleTravelRule,
)
from app.services.detection.result import DetectionResult
from app.services.detection.suspicious_login_rule import (
    SuspiciousLoginRule,
)
from app.services.detection_rule_config_service import (
    is_detection_rule_enabled,
)


rules = [
    BruteForceRule(),
    EventBurstRule(),
    SuspiciousLoginRule(),
    ImpossibleTravelRule(),
]


async def run_detection(
    db: AsyncSession,
    context: DetectionContext,
) -> list[DetectionResult]:
    """Run all enabled detection rules against the supplied context."""

    triggered_results: list[DetectionResult] = []

    for rule in rules:
        rule_enabled = await is_detection_rule_enabled(
            db=db,
            rule_name=rule.name,
        )

        if not rule_enabled:
            continue

        result = await rule.evaluate(
            db,
            context,
        )

        if result.triggered:
            triggered_results.append(result)

    return triggered_results