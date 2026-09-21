"use client";

import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import {
    getIncidentResolution,
    upsertIncidentResolution,
} from "@/services/incident-resolution.service";

import type {
    IncidentResolutionUpsert,
} from "@/types/incident-resolution";


/**
 * Query the current investigation resolution for an incident.
 */
export function useIncidentResolution(
    incidentId: number
) {
    return useQuery({
        queryKey: [
            "incident-resolution",
            incidentId,
        ],
        queryFn: () =>
            getIncidentResolution(incidentId),
        enabled:
            Number.isInteger(incidentId)
            && incidentId > 0,
    });
}


/**
 * Create or update an incident resolution.
 *
 * After the backend transaction succeeds, refresh both the resolution
 * resource and the incident activity timeline so the UI immediately
 * reflects RESOLUTION_ADDED or RESOLUTION_UPDATED activity records.
 */
export function useUpsertIncidentResolution(
    incidentId: number
) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (
            resolution: IncidentResolutionUpsert
        ) =>
            upsertIncidentResolution(
                incidentId,
                resolution
            ),

        onSuccess: async () => {
            await Promise.all([
                queryClient.invalidateQueries({
                    queryKey: [
                        "incident-resolution",
                        incidentId,
                    ],
                }),

                queryClient.invalidateQueries({
                    queryKey: [
                        "incident-activities",
                        incidentId,
                    ],
                }),
            ]);
        },
    });
}