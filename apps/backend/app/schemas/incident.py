from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.incident import IncidentStatus


class IncidentCreate(BaseModel):
    title: str
    description: str
    severity: str
    event_id: int

class IncidentAssign(BaseModel):
    user_id: int


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    status: IncidentStatus
    assigned_to: str | None #temporary legacy display field
    assigned_user_id: int | None  #actual database user assignment
    event_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
