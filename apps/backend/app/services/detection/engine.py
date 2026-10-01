#Orchestrates execution of security detection rules.

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.detection.base import DetectionContext
from app.services.detection.brute_force_rule import (
    BruteForceRule
)
from app.services.detection.event_burst_rule import EventBurstRule
from app.services.detection.result import DetectionResult

rules = [
    BruteForceRule(),
    EventBurstRule(),
]

async def run_detection(
    db: AsyncSession,
    context: DetectionContext,
) -> list[DetectionResult]:
    # Run all registered detection rules against the supplied context.
    
    triggered_results: list[DetectionResult] = []

    for rule in rules:
        result = await rule.evaluate(
            db,
            context
        )

        if result.triggered:
            triggered_results.append(result)

    return triggered_results