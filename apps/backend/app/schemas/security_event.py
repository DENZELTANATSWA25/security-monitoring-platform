from datetime import datetime

from pydantic import BaseModel

from app.models.security_event import EventSeverity



class SecurityEventCreate(BaseModel):

    event_type: str

    severity: EventSeverity

    source: str

    message: str

    user_id: int | None = None



class SecurityEventResponse(BaseModel):

    id: int

    event_type: str

    severity: EventSeverity

    source: str

    message: str

    user_id: int | None

    timestamp: datetime


    class Config:
        from_attributes = True