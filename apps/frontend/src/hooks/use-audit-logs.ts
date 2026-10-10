"use client";

import { useQuery } from "@tanstack/react-query";

import { getAuditLogs } from "@/services/audit.service";

import type { AuditLogFilters } from "@/types/audit";

export function useAuditLogs(
    filters: AuditLogFilters,
    enabled = true,
) {
    return useQuery({
        queryKey: ["audit-logs", filters],
        queryFn: () => getAuditLogs(filters),
        enabled,
        retry: false,
    });
}