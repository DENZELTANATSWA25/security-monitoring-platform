"use client";

import { useQuery } from "@tanstack/react-query";

import { getSecurityReport } from "@/services/reports.service";

export function useSecurityReport() {
    return useQuery({
        queryKey: ["security-report"],
        queryFn: getSecurityReport,
        refetchInterval: 10000,
        refetchOnWindowFocus: true
    });
}