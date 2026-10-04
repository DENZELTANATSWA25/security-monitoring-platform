"""Validated parameter schemas for configurable detection rules."""

from pydantic import BaseModel, ConfigDict, Field


class DetectionRuleParameters(BaseModel):
    """Base contract for persisted detection-rule parameters."""

    model_config = ConfigDict(
        extra="forbid",
    )


class BruteForceParameters(DetectionRuleParameters):
    """Runtime parameters for brute-force detection."""

    failed_attempts_threshold: int = Field(
        default=5,
        ge=1,
    )


class EventBurstParameters(DetectionRuleParameters):
    """Runtime parameters for event-burst detection."""

    event_threshold: int = Field(
        default=5,
        ge=1,
    )

    window_minutes: int = Field(
        default=5,
        ge=1,
    )


class ImpossibleTravelParameters(DetectionRuleParameters):
    """Runtime parameters for impossible-travel detection."""

    max_travel_speed_kmh: float = Field(
        default=1000.0,
        gt=0,
    )

    min_distance_km: float = Field(
        default=100.0,
        ge=0,
    )


class SuspiciousLoginParameters(DetectionRuleParameters):
    """Suspicious-login detection currently has no parameters."""

    pass