"use client";

import { useQuery } from "@tanstack/react-query";

import {
    getIncidents,
    getIncident
} from "@/services/incident.service";

export function useIncidents() {
    return useQuery({
        queryKey: ["incidents"],
        queryFn: getIncidents,
    });
}

export function useIncident(
    id: number
) {
    return useQuery({
        queryKey: ["incident", id],
        queryFn: () => getIncident(id),
        enabled: !!id
    });
}