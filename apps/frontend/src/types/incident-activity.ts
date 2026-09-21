import type{ UserRole } from "@/types/user";

export type IncidentActivityType =
    | "INCIDENT_CREATED"
    | "ASSIGNED"
    | "STATUS_CHANGED"
    | "NOTE_ADDED"
    | "EVENT_LINKED"
    | "ALERT_LINKED"
    | "EVIDENCE_ADDED"
    | "RESOLUTION_ADDED"
    | "RESOLUTION_UPDATED";

export interface IncidentActivityActor {
    id: number;
    full_name: string;
    role: UserRole;
}
export interface IncidentActivity {
    id: number;
    incident_id: number;
    actor_user_id: number | null;
    actor: IncidentActivityActor | null;
    activity_type: IncidentActivityType;
    description: string;
    old_value: string | null;
    new_value: string | null;
    created_at: string;
}