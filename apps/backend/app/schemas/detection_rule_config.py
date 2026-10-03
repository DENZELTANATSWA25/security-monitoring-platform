"""Schemas for managing detection rule configuration."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

class DetectionRuleConfigUpdate(BaseModel):
    """Request used by an administrator to enable or disable a rule."""

    is_enabled: bool

class DetectionRuleConfigResponse(BaseModel):
    """Public representation of a configured detection rule."""

    id: int
    rule_name: str
    display_name: str
    description: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )