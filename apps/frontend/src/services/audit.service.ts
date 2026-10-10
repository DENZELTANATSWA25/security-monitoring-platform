import { api } from "./api";

import type {
    AuditLog,
    AuditLogFilters,
} from "@/types/audit";

export async function getAuditLogs(
    filters: AuditLogFilters = {}
): Promise<AuditLog[]> {
    const response = await api.get<AuditLog[]>(
        "/audit",
        {
            params: filters,
        }
    );

    return response.data;
}