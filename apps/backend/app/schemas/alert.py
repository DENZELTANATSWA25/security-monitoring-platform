from datetime import datetime
from pydantic import BaseModel


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str | None
    resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True