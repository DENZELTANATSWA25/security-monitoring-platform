import { UserRole } from "@/types/user";

export interface IncidentNoteAuthor {
    id: number;
    full_name: string;
    role: UserRole;
}

export interface IncidentNote {
    id: number;
    incident_id: number;
    author_user_id: number | null;
    author: IncidentNoteAuthor | null;
    content: string;
    created_at: string;
    updated_at: string;
} 

export interface IncidentNoteCreate {
    content: string;
}