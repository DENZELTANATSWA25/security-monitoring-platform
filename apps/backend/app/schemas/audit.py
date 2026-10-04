"""Schemas for application audit logs."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Public representation of an application audit log."""

    id: int
    user_id: int | None
    action: str
    resource: str | None
    details: str | None
    timestamp: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
