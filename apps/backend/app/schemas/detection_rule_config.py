"""Schemas for managing detection rule configuration."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DetectionRuleConfigUpdate(BaseModel):
    """Partial administrative update for a detection rule."""

    is_enabled: bool | None = None
    parameters: dict[str, Any] | None = None

    model_config = ConfigDict(
        extra="forbid",
    )


class DetectionRuleConfigResponse(BaseModel):
    """Public representation of a configured detection rule."""

    id: int
    rule_name: str
    display_name: str
    description: str
    is_enabled: bool
    parameters: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )