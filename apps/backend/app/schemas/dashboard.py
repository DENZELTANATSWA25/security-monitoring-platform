from pydantic import BaseModel

class DashboardSummary(BaseModel):
    total_events: int
    critical_events: int
    active_alerts: int
    resolved_alerts: int
    failed_logins_24h: int
    successful_logins_24h: int