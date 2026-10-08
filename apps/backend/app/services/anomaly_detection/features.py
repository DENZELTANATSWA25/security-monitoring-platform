"""Feature extraction for security-event anomaly detection."""

from dataclasses import dataclass

from app.models.security_event import EventSeverity, SecurityEvent


SEVERITY_SCORES: dict[EventSeverity, float] = {
    EventSeverity.INFO: 0.0,
    EventSeverity.WARNING: 1.0,
    EventSeverity.ERROR: 2.0,
    EventSeverity.CRITICAL: 3.0,
}


@dataclass(frozen=True)
class EventFeatures:
    """Numerical features extracted from a security event."""

    severity_score: float
    hour_of_day: float
    day_of_week: float
    has_user: float
    has_telemetry_source: float
    metadata_field_count: float
    message_length: float

    def as_vector(self) -> list[float]:
        """Return features in the stable order expected by the ML model."""

        return [
            self.severity_score,
            self.hour_of_day,
            self.day_of_week,
            self.has_user,
            self.has_telemetry_source,
            self.metadata_field_count,
            self.message_length,
        ]


def extract_event_features(
    event: SecurityEvent,
) -> EventFeatures:
    """Convert a security event into deterministic numerical features."""

    timestamp = event.occurred_at or event.created_at
    metadata = event.event_metadata or {}

    return EventFeatures(
        severity_score=SEVERITY_SCORES[event.severity],
        hour_of_day=float(timestamp.hour),
        day_of_week=float(timestamp.weekday()),
        has_user=1.0 if event.user_id is not None else 0.0,
        has_telemetry_source=(
            1.0
            if event.telemetry_source_id is not None
            else 0.0
        ),
        metadata_field_count=float(len(metadata)),
        message_length=float(len(event.message)),
    )