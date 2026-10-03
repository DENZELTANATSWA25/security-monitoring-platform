# Schemas for external telemetry ingestion.

from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.security_event import EventSeverity


class TelemetryEventCreate(BaseModel):
    # Telemetry supplied by an external system or monitoring agent.

    event_type: str = Field(
        min_length=1,
        max_length=100,
    )

    severity: EventSeverity

    source: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        min_length=1,
        max_length=10_000,
    )

    occurred_at: datetime | None = None

    event_metadata: dict[str, Any] | None = None

    @field_validator(
        "event_type",
        "source",
        "description",
        mode="before",
    )
    @classmethod
    def reject_blank_strings(cls,value: Any) -> Any:
        """ Reject telemetrytext fields containing only whitespace. """

        if isinstance(value, str) and not value.strip():
            raise ValueError("Must not be blank.")
        
        return value

    @field_validator("occurred_at")
    @classmethod
    def validate_occurred_at(
        cls,
        value: datetime | None,
    ) -> datetime | None:
        """
        Reject event timestamps implausibly far in the future.

        A small clock-skew allowance prevents legitimate producers with slightly inaccurate clocks from being rejected
        """

        if value is None:
            return None

        # Compare like with like because Pydantic accepts both naive and timezone-aware ISO 8601 datetimes.
        if value.tzinfo is None:
            now = datetime.now()
        else:
            now = datetime.now(timezone.utc)

        if value > now + timedelta(minutes=5):
            raise ValueError(
                "occured_at cannot be more than 5 minutes in the future."
            )

        return value
