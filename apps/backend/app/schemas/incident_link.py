from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.security_event import EventSeverity

class LinkedByUserResponse(BaseModel):
    # Minimal information about the user who created a linkage
    id: int
    full_name: str

    class Config:
        from_attributes = True

class LinkedSecurityEventResponse(BaseModel):
    #Security event information exposed through an incident linkage
    id: int
    event_type: str
    severity: EventSeverity
    source: str
    message: str
    user_id: int | None
    event_metadata: dict[str, Any] | None
    created_at: datetime

    class Config:
        from_attributes = True

class LinkedAlertResponse(BaseModel):
    #Alert information exposed through a linkage
    id: int
    alert_type: str
    severity: str
    message: str | None
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True

class IncidentEventLinkResponse(BaseModel):
    # Response representation of an event linked to an incident
    id: int
    incident_id: int
    event_id: int
    linked_by_user_id: int | None
    event: LinkedSecurityEventResponse
    linked_by: LinkedByUserResponse | None
    created_at: datetime

    class Config:
        from_attributes = True

class IncidentAlertLinkResponse(BaseModel):
    # Response representation of an alert linked to an incident
    id: int
    incident_id: int
    alert_id: int
    linked_by_user_id: int | None
    alert: LinkedAlertResponse
    linked_by: LinkedByUserResponse | None
    created_at: datetime

    class Config:
        from_attributes = True