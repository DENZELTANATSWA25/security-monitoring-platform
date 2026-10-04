"""Detection rule for geographically impossible successful logins."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_attempt import LoginAttempt
from app.services.detection.base import (
    DetectionContext,
    DetectionRule,
)
from app.services.detection.geo import haversine_distance_km
from app.services.detection.result import DetectionResult

class ImpossibleTravelRule(DetectionRule):
    """
    Detect successful logins whose implied travel speed is unrealistic.

    The rule compares the current successful login with the account's most
    recent previous successful login that contains geographic coordinates.
    """

    name = "IMPOSSIBLE_TRAVEL"

    MAX_TRAVEL_SPEED_KMH = 1000.0
    MIN_DISTANCE_KM = 100.0

    def __init__(
        self,
        *,
        max_travel_speed_kmh: float | None = None,
        min_distance_km: float | None = None,
    ) -> None:
        self.max_travel_speed_kmh = (
            max_travel_speed_kmh
            if max_travel_speed_kmh is not None
            else self.MAX_TRAVEL_SPEED_KMH
        )

        self.min_distance_km = (
            min_distance_km
            if min_distance_km is not None
            else self.MIN_DISTANCE_KM
        )

    async def evaluate(
        self,
        db: AsyncSession,
        context: DetectionContext,
    ) -> DetectionResult:
        attempt = context.login_attempt

        # This rule applies only to successful authentication attempts.
        if attempt is None or not attempt.successful:
            return DetectionResult.not_triggered()

        # Location data is required for geographic comparison.
        if attempt.latitude is None or attempt.longitude is None:
            return DetectionResult.not_triggered()

        previous_result = await db.execute(
            select(LoginAttempt)
            .where(
                LoginAttempt.email == attempt.email,
                LoginAttempt.successful.is_(True),
                LoginAttempt.latitude.is_not(None),
                LoginAttempt.longitude.is_not(None),
                LoginAttempt.id != attempt.id,
                LoginAttempt.timestamp <= attempt.timestamp,
            )
            .order_by(
                LoginAttempt.timestamp.desc(),
                LoginAttempt.id.desc(),
            )
            .limit(1)
        )

        previous_attempt = previous_result.scalar_one_or_none()

        # There is no geographic history to compare against.
        if previous_attempt is None:
            return DetectionResult.not_triggered()

        distance_km = haversine_distance_km(
            previous_attempt.latitude,
            previous_attempt.longitude,
            attempt.latitude,
            attempt.longitude,
        )

        # Ignore small geographic movements.
        if distance_km < self.min_distance_km:
            return DetectionResult.not_triggered()

        elapsed_seconds = (
            attempt.timestamp - previous_attempt.timestamp
        ).total_seconds()

        # A non-positive interval cannot produce a meaningful travel speed.
        if elapsed_seconds <= 0:
            return DetectionResult.not_triggered()

        elapsed_hours = elapsed_seconds / 3600

        implied_speed_kmh = distance_km / elapsed_hours

        if implied_speed_kmh <= self.max_travel_speed_kmh:
            return DetectionResult.not_triggered()

        return DetectionResult.triggered_alert(
            alert_type=self.name,
            severity="HIGH",
            message=(
                f"Impossible travel detected for {attempt.email}: "
                f"approximately {distance_km:.0f} km travelled in "
                f"{elapsed_hours:.2f} hours "
                f"({implied_speed_kmh:.0f} km/h implied speed)"
            ),
        )