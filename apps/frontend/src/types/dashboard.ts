export interface DashboardSummary {
    total_events: number;
    critical_events: number;
    active_alerts: number;
    resolved_alerts: number;
    failed_logins_24h: number;
    successful_logins_24h: number;
}