from sqlalchemy.ext.asyncio import AsyncSession

from app.services.detection.base import DetectionRule
from app.services.login_attempt_service import count_failed_attempts

class BruteForceRule(DetectionRule):
    """Detect repeated failed authentication attempts for an account."""

    name = "BRUTE_FORCE_ATTACK"

    async def evaluate(
            self,
            db: AsyncSession,
            context: dict
    ):
        email = context.get("email")

        # This rule only applies when an account/email is known.
        if not email:
            return {
                "triggered": False
            }
        
        failed_count = await count_failed_attempts(
            db,
            email
        )

        if failed_count >= 5:
            return {
                "triggered": True,
                "alert_type": "BRUTE_FORCE_ATTACK",
                "severity": "CRITICAL",
                "message": f"Brute force attack detected on {email}"
            }
        
        return {
            "triggered": False
        }