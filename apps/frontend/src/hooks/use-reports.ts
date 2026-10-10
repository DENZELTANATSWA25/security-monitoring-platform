"use client";

import { useQuery } from "@tanstack/react-query";

import { getSecurityReport } from "@/services/reports.service";

export function useSecurityReport() {
    return useQuery({
        queryKey: ["security-report"],
        queryFn: getSecurityReport,
        refetchInterval: 30000,
        refetchOnWindowFocus: true,
        retry: 1,
    });
}