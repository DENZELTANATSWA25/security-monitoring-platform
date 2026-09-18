"use client";

import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import {
    getIncidentAlertLinks,
    getIncidentEventLinks,
    linkAlertToIncident,
    linkEventToIncident,
} from "@/services/incident-links.service";

/**
 * Query additional security eevents linked during investigation.
 */
export function useIncidentEventLinks(
    incidentId: number
) {
    return useQuery({
        queryKey: [
            "incident-events",
            incidentId,
        ],
        queryFn: () =>
            getIncidentEventLinks(incidentId),
        enabled:
            Number.isInteger(incidentId)
            && incidentId > 0,
    })
}

/**
 * Query alerts linked during investigation.
 */
export function useIncidentAlertLinks(
    incidentId: number
) {
    return useQuery({
        queryKey: [
            "incident-alerts",
            incidentId,
        ],
        queryFn: () =>
            getIncidentAlertLinks(incidentId),
        enabled:
            Number.isInteger(incidentId)
            && incidentId > 0,
    })
}

/**
 * Link an additional security event and refresh both the investigation evidence and activity timeline after the backend transaction succeeds.
 */

export function useLinkEventToIncident(

    incidentId: number

) {

    const queryClient = useQueryClient();

    return useMutation({

        mutationFn: (eventId: number) =>

            linkEventToIncident(

                incidentId,

                eventId

            ),

        onSuccess: async () => {

            await Promise.all([

                queryClient.invalidateQueries({

                    queryKey: [

                        "incident-events",

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

/**
 * Link an alert and refresh both the investigation evidence and activity timeline after the backend transaction succeeds.
 */

export function useLinkAlertToIncident(

    incidentId: number

) {

    const queryClient = useQueryClient();

    return useMutation({

        mutationFn: (alertId: number) =>

            linkAlertToIncident(

                incidentId,

                alertId

            ),

        onSuccess: async () => {

            await Promise.all([

                queryClient.invalidateQueries({

                    queryKey: [

                        "incident-alerts",

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