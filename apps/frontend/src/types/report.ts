export interface DistributionItem {
  name: string;
  count: number;
}

export interface SecurityReport {
  total_events: number;
  critical_events: number;
  active_alerts: number;
  resolved_alerts: number;
  failed_logins_24h: number;
  successful_logins_24h: number;
  
  severity_distribution: DistributionItem[];
  event_type_distribution: DistributionItem[];
  alert_severity_distribution: DistributionItem[];
}