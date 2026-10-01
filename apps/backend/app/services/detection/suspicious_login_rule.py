# Detection rule for successful loginns from previously unseen IP addresses.

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_attempt import LoginAttempt
from app.services.detection.base import (
    DetectionContext,
    DetectionRule,
)
from app.services.detection.result import DetectionResult

class SuspiciousLoginRule(DetectionRule):
    """
    Detect a successful login from a previously unseen IP addresses.

    The first successful login for an account establishes its initial IP history and is therefore not considered suspicious.
    """

    name = "SUSPICIOUS_LOGIN"

    async def evaluate(
            self,
            db: AsyncSession,
            context: DetectionContext,
    ) -> DetectionResult:
        attempt = context.login_attempt

        # Thisrule only applies to succesful authentication attempts.
        if attempt is None or not attempt.successful:
            return DetectionResult.not_triggered()

        # The current attempt has already been flushed. Exclude it from historical queries so that it does not count as its own history.
        previous_success_count_result = await db.execute(
            select(func.count(LoginAttempt.id))
            .where(
                LoginAttempt.email == attempt.email,
                LoginAttempt.successful.is_(True),
                LoginAttempt.id != attempt.id,
            )
        )

        previous_success_count = (
            previous_success_count_result.scalar_one()
        )

        # The first successful login establishes the account's baseline.
        if previous_success_count == 0:
            return DetectionResult.not_triggered()

        known_ip_result = await db.execute(
            select(func.count(LoginAttempt.id))
            .where(
                LoginAttempt.email == attempt.email,
                LoginAttempt.successful.is_(True),
                LoginAttempt.ip_address == attempt.ip_address,
                LoginAttempt.id != attempt.id,
            )
        )

        previous_ip_count = known_ip_result.scalar_one()

        if previous_ip_count > 0:
            return DetectionResult.not_triggered()

        return DetectionResult.triggered_alert(
            alert_type=self.name,
            severity="MEDIUM",
            message=(
                F"Successful login for {attempt.email} from "
                f"previously unseen IP address {attempt.ip_address}"
            ),
        )