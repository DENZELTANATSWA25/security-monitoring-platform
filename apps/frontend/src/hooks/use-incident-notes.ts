import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import {
    createIncidentNote,
    getIncidentNotes,
} from "@/services/incident-notes.service";


export function useIncidentNotes(
    incidentId: number
) {
    return useQuery({
        queryKey: [
            "incident-notes",
            incidentId,
        ],
        queryFn: () =>
            getIncidentNotes(incidentId),
        enabled:
            Number.isFinite(incidentId)
            && incidentId > 0,
    });
}


export function useCreateIncidentNote(
    incidentId: number
) {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: (content: string) =>
            createIncidentNote(
                incidentId,
                { content }
            ),

        onSuccess: async () => {
            // Refresh the investigation notes.
            await queryClient.invalidateQueries({
                queryKey: [
                    "incident-notes",
                    incidentId,
                ],
            });

            // Adding a note also creates a NOTE_ADDED
            // incident activity on the backend.
            await queryClient.invalidateQueries({
                queryKey: [
                    "incident-activities",
                    incidentId,
                ],
            });
        },
    });
}