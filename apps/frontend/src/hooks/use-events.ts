"use client";

import {
    useQuery,
    type UseQueryOptions,
} from "@tanstack/react-query";

import {
    getEvents,
    getEventById,
    type EventQueryParams,
} from "@/services/events.service";

import type { SecurityEvent } from "@/types/event";

type EventQueryOptions = Pick<
    UseQueryOptions<SecurityEvent[]>,
    "enabled"
>;

export function useEvents(
    params: EventQueryParams = {},
    options: EventQueryOptions = {}
) {
    return useQuery({
        queryKey: ["security-events", params],
        queryFn: () => getEvents(params),
        refetchInterval: 5000,
        refetchOnWindowFocus: true,
        ...options,
    });
}

export function useEvent(
    eventId: number
) {
    return useQuery({
        queryKey: ["security-event", eventId],
        queryFn: () => getEventById(eventId),
        enabled:
            Number.isInteger(eventId) &&
            eventId > 0,
        staleTime: 30_000,
    });
}