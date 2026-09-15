"use client";

import { useQuery } from "@tanstack/react-query";

import {
    getIncidentActivities,
} from "@/services/incident-activity.service";

export function useIncidentActivities(
    incidentId: number
) {
    return useQuery({
        queryKey: [
            "incident-activities",
            incidentId
        ],
        queryFn: () =>
            getIncidentActivities(incidentId),
        enabled: Number.isInteger(incidentId)
            && incidentId > 0,
    });
}