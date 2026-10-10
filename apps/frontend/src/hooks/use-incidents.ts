"use client";

import { useQuery } from "@tanstack/react-query";

import {
    getIncidents,
    getIncident,
    type IncidentQueryParams,
} from "@/services/incident.service";

export function useIncidents(
    params: IncidentQueryParams = {}
) {
    return useQuery({
        queryKey: ["incidents", params],
        queryFn: () => getIncidents(params),
        refetchInterval: 5000,
        refetchOnWindowFocus: true,
    });
}

export function useIncident(
    id: number
) {
    return useQuery({
        queryKey: ["incident", id],
        queryFn: () => getIncident(id),
        enabled: Number.isInteger(id) && id > 0,
    });
}