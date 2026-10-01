# Schemas for external telemetry ingestion.

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

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
    )

    occurred_at: datetime | None = None

    event_metadata: dict[str, Any] | None = None