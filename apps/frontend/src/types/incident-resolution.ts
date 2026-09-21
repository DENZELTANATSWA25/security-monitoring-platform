import type { UserRole } from "@/types/user";

export type ResolutionClassification = 
    | "TRUE_POSITIVE"
    | "FALSE_POSITIVE"
    | "BENIGN"
    | "DUPLICATE"
    | "INCONCLUSIVE";

export interface IncidentResolutionAuthor {
    id: number;
    full_name: string;
    role: UserRole;
}

export interface IncidentResolution {
    id: number;
    incident_id: number;
    classification: ResolutionClassification;
    summary: string;
    root_cause: string | null;
    remediation: string | null;
    resolved_by_user_id: number | null;
    resolved_by: IncidentResolutionAuthor | null;
    created_at: string;
    updated_at: string;
}

export interface IncidentResolutionUpsert {
    classification: ResolutionClassification;
    summary: string;
    root_cause: string | null;
    remediation: string | null;
}