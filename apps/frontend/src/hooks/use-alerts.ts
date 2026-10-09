"use client";

import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import {
    getAlerts,
    resolveAlert,
} from "@/services/alerts.service";

export function useAlerts() {
    return useQuery({
        queryKey: ["alerts"],
        queryFn: getAlerts,
        refetchInterval: 5000,
        refetchOnWindowFocus: true,
    });
}

export function useResolveAlert() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: resolveAlert,
        onSuccess: async () => {
            await Promise.all([
                queryClient.invalidateQueries({
                    queryKey: ["alerts"],
                }),
                queryClient.invalidateQueries({
                    queryKey: ["dashboard-summary"],
                }),
            ]);
        },
    });
}