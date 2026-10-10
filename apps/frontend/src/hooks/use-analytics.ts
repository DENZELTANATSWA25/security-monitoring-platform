"use client";

import { useQuery } from "@tanstack/react-query";

import { getEventTrend } from "@/services/analytics.service";

export function useAnalytics() {
    return useQuery({
        queryKey: ["event-trend"],
        queryFn: getEventTrend,
        refetchInterval: 30000,
        refetchOnWindowFocus: true,
        retry: 1,
    });
}