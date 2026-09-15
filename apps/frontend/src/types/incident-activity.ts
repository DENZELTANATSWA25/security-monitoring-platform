import type{ UserRole } from "@/types/user";

export type IncidentActivityType =
    | "INCIDENT_CREATED"
    | "ASSIGNED"
    | "STATUS_CHANGED"
    | "NOTE_ADDED";

export interface IncidentActivityActor {
    id: number;
    full_name: string;
    role: UserRole;
}
export interface IncidentActivity {
    id: number;
    incident_id: number;
    actor_user_id: number;
    actor: IncidentActivityActor;
    activity_type: IncidentActivityType;
    description: string;
    old_value: string | null;
    new_value: string | null;
    created_at: string;
}