"use client";

import {
    useMutation,
    useQuery,
    useQueryClient,
    type UseQueryOptions,
} from "@tanstack/react-query";

import {
    getAlerts,
    getAlertById,
    resolveAlert,
    type AlertQueryParams,
} from "@/services/alerts.service";

import type { Alert } from "@/types/alert";

type AlertQueryOptions = Pick<
    UseQueryOptions<Alert[]>,
    "enabled"
>;

export function useAlerts(
    params: AlertQueryParams = {},
    options: AlertQueryOptions = {}
) {
    return useQuery({
        queryKey: ["alerts", params],
        queryFn: () => getAlerts(params),
        refetchInterval: 5000,
        refetchOnWindowFocus: true,
        ...options,
    });
}

export function useAlertDetails(
    id: number | null
) {
    return useQuery({
        queryKey: ["alert-details", id],
        queryFn: () => getAlertById(id!),
        enabled: id !== null,
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

                queryClient.invalidateQueries({
                    queryKey: ["alert-details"],
                }),
            ]);
        },
    });
}