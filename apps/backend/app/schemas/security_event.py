from datetime import datetime

from pydantic import BaseModel

from app.models.security_event import EventSeverity



class SecurityEventCreate(BaseModel):

    event_type: str

    severity: EventSeverity

    source: str

    description: str

    user_id: int | None = None

    event_metadata: dict | None = None


class SecurityEventResponse(BaseModel):

    id: int

    created_at: datetime


    class Config:
        from_attributes = True