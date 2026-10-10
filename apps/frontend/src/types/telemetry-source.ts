export type TelemetryHealthStatus = 
  | "ONLINE"
  | "OFFLINE"
  | "NEVER_CONNECTED"
  | "REVOKED";

export interface TelemetrySource {
  id: number;
  name: string;
  source_type: string;
  key_id: string;
  is_active: boolean;
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TelemetrySourceCreate {
    name: string;
    source_type: string;
}

export interface TelemetrySourceCredentialResponse
    extends TelemetrySource {
        credential: string;
    }

export interface TelemetrySourceStatus {
    id: number;
    name: string;
    source_type: string;
    is_active: boolean;
    health_status: TelemetryHealthStatus;
    last_seen_at: string | null;
    events_24h: number;
    last_event_at: string | null;
}