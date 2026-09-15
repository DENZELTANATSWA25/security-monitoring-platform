from datetime import datetime

from pydantic import BaseModel

from app.models.incident_activity import IncidentActivityType
from app.models.user import UserRole

class IncidentActivityActor(BaseModel):
    id: int
    full_name: str
    role: UserRole

    class Config:
        from_attributes = True

class IncidentActivityResponse(BaseModel):
    id: int
    incident_id: int
    actor_user_id: int | None
    actor: IncidentActivityActor | None
    activity_type: IncidentActivityType
    description: str
    old_value: str | None
    new_value: str | None
    created_at: datetime

    class Config:
        from_attributes = True