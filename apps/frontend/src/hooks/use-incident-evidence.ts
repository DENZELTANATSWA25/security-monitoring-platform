"use client";

import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import {
    addIncidentEvidence,
    getIncidentEvidence,
} from "@/services/incident-evidence.service";

import type {
    IncidentEvidenceCreate,
} from "@/types/incident-evidence";

/**
 * Query investigation evidence associated with an incident.
 */
export function useIncidentEvidence(
    incidentId: number
) {
    return useQuery({
        queryKey: [
            "incident-evidence",
            incidentId,
        ],
        queryFn: () => 
            getIncidentEvidence(incidentId),
        enabled:
            Number.isInteger(incidentId)
            && incidentId > 0,
    });
}

/**
 * Add evidence and refresh both the evidence collection and the incident activity timeline after the backend transaction succeeds.
 */
export function useAddIncidentEvidence(
    incidentId: number,
) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (
            evidence: IncidentEvidenceCreate
        ) =>
            addIncidentEvidence(
                incidentId,
                evidence
            ),
        
        onSuccess: async () => {
            await Promise.all([
                queryClient.invalidateQueries({
                    queryKey: [
                        "incident-evidence",
                        incidentId,
                    ],
                }),
                
                queryClient.invalidateQueries({
                    queryKey: [
                        "incident-activity",
                        incidentId,
                    ],
                }),
            ]);
        },
    });
}