export type IncidentStatus = 
| "OPEN"
| "IN_PROGRESS"
| "RESOLVED"
| "CLOSED";

export interface Incident {
    id: number;
    title: string;
    description: string;
    severity: string;
    status: IncidentStatus;
    assigned_to: string | null;
    event_id: number | null;
    created_at: string;
    updated_at: string;
}

export interface IncidentCreate {
    title: string;
    description: string;
    severity: string;
    event_id?: number | null;
}