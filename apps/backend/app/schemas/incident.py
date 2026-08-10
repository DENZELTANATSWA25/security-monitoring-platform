from datetime import datetime

from pydantic import BaseModel

from app.models.incident import IncidentStatus


class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str
    event_id: int | None = None

class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    status: IncidentStatus
    assigned_to: str | None
    event_id: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True