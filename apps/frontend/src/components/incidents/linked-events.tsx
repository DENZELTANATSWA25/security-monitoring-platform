"use client";

import { useMemo, useState } from "react";
import axios from "axios";

import { useEvents } from "@/hooks/use-events";
import {
    useIncidentEventLinks,
    useLinkEventToIncident,
} from "@/hooks/use-incident-links";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";


interface LinkedEventsProps {
    incidentId: number;
    originatingEventId: number;
    canManage: boolean;
}


function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}


function getErrorMessage(error: unknown) {
    if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
            return detail;
        }
    }

    return "Unable to link the security event.";
}


export default function LinkedEvents({
    incidentId,
    originatingEventId,
    canManage,
}: LinkedEventsProps) {
    const [selectedEventId, setSelectedEventId] =
        useState("");

    const [mutationError, setMutationError] =
        useState<string | null>(null);

    const {
        data: links = [],
        isLoading,
        error,
    } = useIncidentEventLinks(incidentId);

    const {
        data: events = [],
        isLoading: isLoadingEvents,
    } = useEvents();

    const linkEventMutation =
        useLinkEventToIncident(incidentId);


    /*
     * Analysts should only be offered events that are not:
     * 1. the originating event, or
     * 2. already linked to the investigation.
     */
    const availableEvents = useMemo(() => {
        const linkedEventIds = new Set(
            links.map((link) => link.event_id)
        );

        return events.filter(
            (event) =>
                event.id !== originatingEventId
                && !linkedEventIds.has(event.id)
        );
    }, [
        events,
        links,
        originatingEventId,
    ]);


    async function handleLinkEvent() {
        if (!selectedEventId) {
            return;
        }

        const eventId = Number(selectedEventId);

        if (!Number.isInteger(eventId)) {
            return;
        }

        try {
            setMutationError(null);

            await linkEventMutation.mutateAsync(
                eventId
            );

            setSelectedEventId("");
        } catch (mutationFailure) {
            setMutationError(
                getErrorMessage(mutationFailure)
            );
        }
    }


    return (
        <Card>
            <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <CardTitle>
                            Linked Events
                        </CardTitle>

                        <p className="mt-1 text-sm text-muted-foreground">
                            Additional security events collected as
                            investigation evidence.
                        </p>
                    </div>

                    <Badge variant="outline">
                        {links.length} linked
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="space-y-6">
                {canManage && (
                    <div className="space-y-2">
                        <div className="flex flex-col gap-3 sm:flex-row">
                            <Select
                                value={selectedEventId}
                                onValueChange={(value) => {
                                    setSelectedEventId(
                                        value ?? ""
                                    );

                                    setMutationError(null);
                                }}
                                disabled={
                                    isLoadingEvents
                                    || linkEventMutation.isPending
                                    || availableEvents.length === 0
                                }
                            >
                                <SelectTrigger className="w-full">
                                    <SelectValue
                                        placeholder={
                                            isLoadingEvents
                                                ? "Loading events..."
                                                : availableEvents.length === 0
                                                    ? "No additional events available"
                                                    : "Select an event to link"
                                        }
                                    />
                                </SelectTrigger>

                                <SelectContent>
                                    {availableEvents.map(
                                        (event) => (
                                            <SelectItem
                                                key={event.id}
                                                value={String(event.id)}
                                            >
                                                #{event.id}
                                                {" — "}
                                                {event.event_type}
                                                {" — "}
                                                {event.severity}
                                            </SelectItem>
                                        )
                                    )}
                                </SelectContent>
                            </Select>

                            <Button
                                onClick={handleLinkEvent}
                                disabled={
                                    !selectedEventId
                                    || linkEventMutation.isPending
                                }
                            >
                                {linkEventMutation.isPending
                                    ? "Linking..."
                                    : "Link Event"}
                            </Button>
                        </div>

                        {mutationError && (
                            <p className="text-sm text-red-600">
                                {mutationError}
                            </p>
                        )}
                    </div>
                )}

                {isLoading ? (
                    <p className="text-sm text-muted-foreground">
                        Loading linked events...
                    </p>
                ) : error ? (
                    <p className="text-sm text-red-600">
                        Unable to load linked events.
                    </p>
                ) : links.length === 0 ? (
                    <div className="rounded-md border border-dashed p-6 text-center">
                        <p className="font-medium">
                            No additional events linked
                        </p>

                        <p className="mt-1 text-sm text-muted-foreground">
                            Investigation evidence linked to this
                            incident will appear here.
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {links.map((link) => (
                            <div
                                key={link.id}
                                className="rounded-md border p-4"
                            >
                                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                                    <div className="min-w-0">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <p className="font-semibold">
                                                Event #{link.event.id}
                                                {" — "}
                                                {link.event.event_type}
                                            </p>

                                            <Badge variant="outline">
                                                {link.event.severity}
                                            </Badge>
                                        </div>

                                        <p className="mt-2 text-sm">
                                            {link.event.message}
                                        </p>
                                    </div>

                                    <p className="shrink-0 text-sm text-muted-foreground">
                                        {formatDate(
                                            link.event.created_at
                                        )}
                                    </p>
                                </div>

                                <div className="mt-4 grid gap-4 border-t pt-4 sm:grid-cols-3">
                                    <div>
                                        <p className="text-xs text-muted-foreground">
                                            Source
                                        </p>

                                        <p className="mt-1 text-sm font-medium break-all">
                                            {link.event.source}
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-xs text-muted-foreground">
                                            Linked by
                                        </p>

                                        <p className="mt-1 text-sm font-medium">
                                            {link.linked_by?.full_name
                                                ?? "Unknown user"}
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-xs text-muted-foreground">
                                            Linked
                                        </p>

                                        <p className="mt-1 text-sm font-medium">
                                            {formatDate(
                                                link.created_at
                                            )}
                                        </p>
                                    </div>
                                </div>

                                {link.event.event_metadata
                                    && Object.keys(
                                        link.event.event_metadata
                                    ).length > 0 && (
                                    <div className="mt-4 border-t pt-4">
                                        <p className="mb-2 text-xs text-muted-foreground">
                                            Metadata
                                        </p>

                                        <div className="flex flex-wrap gap-2">
                                            {Object.entries(
                                                link.event.event_metadata
                                            ).map(
                                                ([key, value]) => (
                                                    <Badge
                                                        key={key}
                                                        variant="outline"
                                                    >
                                                        {key.replaceAll(
                                                            "_",
                                                            " "
                                                        )}
                                                        {": "}
                                                        {String(value)}
                                                    </Badge>
                                                )
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}