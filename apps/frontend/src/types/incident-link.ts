import type { Alert } from "@/types/alert";


/**
 * Lightweight user representation returned with an incident linkage.
 */
export interface IncidentLinkUser {
  id: number;
  full_name: string;
}

/**
 * Security event representation returned by the incident-link API.
 * This intentionally mirrors the backend IncidentEventLinkResponse contract instead of reusing the broader SecurityEvent type.
 * The linkage response includes fields such as user_id and nullable event metadata.
 */
export interface IncidentLinkedEvent {
    id: number;
    event_type: string;
    severity:
        | "INFO"
        | "WARNING"
        | "ERROR"
        | "CRITICAL";
    source: string;
    message: string;
    user_id: number | null;
    event_metadata:
        | Record<string, unknown>
        | null;
    created_at: string;
}

/**
 * Additional security event attached to an incident during investigation.
 * The originating event is not represented by this type. It remains stored seperately on Incident.event_id.
 */
export interface IncidentEventLink {
    id: number;
    incident_id: number;
    event_id: number;
    linked_by_user_id: number | null;
    event: IncidentLinkedEvent;
    linked_by: IncidentLinkUser | null;
    created_at: string;
}

/**
 * Alert attached to an incident during investigation.
 */
export interface IncidentAlertLink {
    id: number;
    incident_id: number;
    alert_id: number;
    linked_by_user_id: number | null;
    alert: Alert;
    event: IncidentLinkedEvent;
    linked_by: IncidentLinkUser | null;
    created_at: string;
}
