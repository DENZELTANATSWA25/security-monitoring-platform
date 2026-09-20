import type { UserRole } from "@/types/user";

export type EvidenceType = 
    | "IP_ADDRESS"
    | "DOMAIN"
    | "URL"
    | "FILE_HASH"
    | "USERNAME"
    | "HOSTNAME"
    | "PROCESS"
    | "OTHER";

export interface IncidentEvidenceAuthor {
    id: number;
    full_name: string;
    role: UserRole;
}

export interface IncidentEvidence {
    id: number;
    incident_id: number;
    evidence_type: EvidenceType;
    value: string;
    description: string | null;
    source: string | null;
    added_by_user_id: number | null;
    added_by: IncidentEvidenceAuthor | null;
    created_at: string;
}

export interface IncidentEvidenceCreate {
    evidence_type: EvidenceType;
    value: string;
    description: string | null;
    source?: string | null;
}