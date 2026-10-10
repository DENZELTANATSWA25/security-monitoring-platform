"use client";

import {
    useQuery,
    type UseQueryOptions,
} from "@tanstack/react-query";

import {
    getEvents,
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