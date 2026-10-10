export interface AuditLog {
    id: number;
    user_id: number | null;
    action: string;
    resource: string | null;
    details: string | null;
    timestamp: string;
}

export type AuditSortOrder = "asc" | "desc";

export interface AuditLogFilters {
    limit?: number;
    offset?: number;
    user_id?: number;
    action?: string;
    resource?: string;
    start_date?: string;
    end_date?: string;
    search?: string;
    sort_order?: AuditSortOrder;
}