from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str | None
    resolved: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
