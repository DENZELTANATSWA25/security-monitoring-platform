"""Schemas for managing registered telemetry sources."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TelemetrySourceCreate(BaseModel):
    """Request used by an administrator to register a telemetry source."""

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    source_type: str = Field(
        min_length=1,
        max_length=255,
    )


class TelemetrySourceResponse(BaseModel):
    """Public representation of a registered telemetry source."""

    id: int
    name: str
    source_type: str
    key_id: str
    is_active: bool
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class TelemetrySourceCreatedResponse(TelemetrySourceResponse):
    """
    Response returned only when a telemetry source is created.

    The complete credential is exposed once so it can be securely
    transferred to the external producer. It cannot be recovered later
    because only the secret hash is persisted.
    """

    credential: str
