# Detection rule for repeated failed authentication attempts.

from sqlalchemy.ext.asyncio import AsyncSession
from app.services.detection.base import DetectionRule, DetectionContext

from app.services.detection.result import DetectionResult
from app.services.login_attempt_service import count_failed_attempts

class BruteForceRule(DetectionRule):
    """Detect repeated failed authentication attempts for an account."""

    name = "BRUTE_FORCE_ATTACK"

    FAILED_ATTEMPTS_THRESHOLD = 5

    async def evaluate(
            self,
            db: AsyncSession,
            context: DetectionContext,
    ) -> DetectionResult:
        attempt = context.login_attempt

        if attempt is None or attempt.successful:
            return DetectionResult.not_triggered()

        email = attempt.email
        
        failed_count = await count_failed_attempts(
            db,
            email
        )

        if failed_count < self.FAILED_ATTEMPTS_THRESHOLD:
            return DetectionResult.not_triggered()
        
        return DetectionResult.triggered_alert(
            alert_type=self.name,
            severity="CRITICAL",
            message=f"Brute force attack detected on {email}"
        )