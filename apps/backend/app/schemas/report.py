from pydantic import BaseModel

class DistributionItem(BaseModel):
    name: str
    count: int

class SecurityReportResponse(BaseModel):
    total_events: int
    critical_events: int
    active_alerts: int
    resolved_alerts: int
    failed_logins_24h: int
    successful_logins_24h: int
    severity_distribution: list[DistributionItem]
    event_type_distribution: list[DistributionItem]
    alert_severity_distribution: list[DistributionItem]