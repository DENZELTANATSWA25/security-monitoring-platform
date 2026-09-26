from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

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

    event_type: str

    severity: EventSeverity

    source: str

    message: str

    user_id: int | None

    event_metadata: dict[str, Any] | None

    created_at: datetime


    model_config = ConfigDict(from_attributes=True)



class SecurityEventListResponse(BaseModel):

    id: int

    event_type: str

    severity: EventSeverity

    source: str

    message: str

    user_id: int | None

    event_metadata: dict[str, Any] | None

    created_at: datetime


    model_config = ConfigDict(from_attributes=True)
