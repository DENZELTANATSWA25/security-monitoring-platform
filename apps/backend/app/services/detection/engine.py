from sqlalchemy.ext.asyncio import AsyncSession

from app.services.detection.brute_force_rule import (
    BruteForceRule
)

rules = [
    BruteForceRule(),
]

async def run_detection(
    db: AsyncSession,
    context: dict
):
    
    results = []

    for rule in rules:
        result = await rule.evaluate(
            db,
            context
        )

        if result["triggered"]:
            results.append(result)

    return results