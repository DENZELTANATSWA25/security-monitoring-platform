# Detection rule. for unusually frequent security events.

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent
from app.services.detection.base import (
    DetectionContext,
    DetectionRule,
)
from app.services.detection.result import DetectionResult

class EventBurstRule(DetectionRule):
    """Detect a burst of security events from the same source."""

    name = "EVENT_BURST"

    EVENT_THRESHOLD = 5
    WINDOW_MINUTES = 5

    def __init__(
        self,
        *,
        event_threshold: int | None = None,
        window_minutes: int | None = None,
    ) -> None:
        self.event_threshold = (
            event_threshold
            if event_threshold is not None
            else self.EVENT_THRESHOLD
        )

        self.window_minutes = (
            window_minutes
            if window_minutes is not None
            else self.WINDOW_MINUTES
        )

    async def evaluate(
        self,
        db: AsyncSession,
        context: DetectionContext,
    ) -> DetectionResult:
        event = context.event

        if event is None:
            return DetectionResult.not_triggered()

        if not event.source:
            return DetectionResult.not_triggered()

        reference_time = event.created_at or datetime.utcnow()

        window_start = reference_time - timedelta(
            minutes=self.window_minutes,
        )

        result = await db.execute(
            select(func.count(SecurityEvent.id))
            .where(
                SecurityEvent.source == event.source,
                SecurityEvent.created_at >= window_start,
                SecurityEvent.created_at <= reference_time,
            )
        )

        event_count = result.scalar_one()

        if event_count < self.event_threshold:
            return DetectionResult.not_triggered()

        return DetectionResult.triggered_alert(
            alert_type=self.name,
            severity="HIGH",
            message=(
                f"High event frequency detected from source "
                f"{event.source}: {event_count} events within "
                f"{self.window_minutes} minutes"
            ),
        )