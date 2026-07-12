import {
    useQuery,
    useMutation,
    useQueryClient
} from "@tanstack/react-query";

import {
    getAlerts,
    resolveAlert
} from "@/services/alerts.service";

export function useAlerts() {
    return useQuery({
        queryKey: ["alerts"],
        queryFn: getAlerts,
        refetchInterval: 5000,
        refetchOnWindowFocus: true
    });
}

export function useResolveAlert() {
    const client = useQueryClient();
    return useMutation({
        mutationFn: resolveAlert,
        onSuccess: () => {
            client.invalidateQueries({
                queryKey: ["alerts"]
            });
        }
    });
}