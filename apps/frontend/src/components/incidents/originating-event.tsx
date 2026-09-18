"use client";

import type { SecurityEvent } from "@/types/event";

import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";


interface OriginatingEventProps {
    eventId: number;
    event?: SecurityEvent;
    isLoading: boolean;
}


function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}


export default function OriginatingEvent({
    eventId,
    event,
    isLoading,
}: OriginatingEventProps) {
    return (
        <Card>
            <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <CardTitle>
                            Originating Event
                        </CardTitle>

                        <p className="mt-1 text-sm text-muted-foreground">
                            The security event that triggered this incident.
                        </p>
                    </div>

                    <Badge variant="outline">
                        Event #{eventId}
                    </Badge>
                </div>
            </CardHeader>

            <CardContent>
                {isLoading ? (
                    <p className="text-sm text-muted-foreground">
                        Loading originating event...
                    </p>
                ) : !event ? (
                    <div className="rounded-md border border-dashed p-4">
                        <p className="font-medium">
                            Event #{eventId}
                        </p>

                        <p className="mt-1 text-sm text-muted-foreground">
                            The originating event could not be found in the
                            current event collection.
                        </p>
                    </div>
                ) : (
                    <div className="space-y-5">
                        <div className="flex flex-wrap items-center gap-2">
                            <p className="text-lg font-semibold">
                                {event.event_type}
                            </p>

                            <Badge variant="outline">
                                {event.severity}
                            </Badge>
                        </div>

                        <p className="text-sm">
                            {event.message}
                        </p>

                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                            <div>
                                <p className="text-sm text-muted-foreground">
                                    Event ID
                                </p>

                                <p className="mt-1 font-medium">
                                    #{event.id}
                                </p>
                            </div>

                            <div>
                                <p className="text-sm text-muted-foreground">
                                    Source
                                </p>

                                <p className="mt-1 font-medium break-all">
                                    {event.source}
                                </p>
                            </div>

                            <div>
                                <p className="text-sm text-muted-foreground">
                                    Detected
                                </p>

                                <p className="mt-1 font-medium">
                                    {formatDate(event.created_at)}
                                </p>
                            </div>
                        </div>

                        {event.event_metadata
                            && Object.keys(event.event_metadata).length > 0 && (
                            <div>
                                <p className="mb-3 text-sm font-medium">
                                    Event Metadata
                                </p>

                                <div className="rounded-md border">
                                    {Object.entries(event.event_metadata).map(
                                        ([key, value]) => (
                                            <div
                                                key={key}
                                                className="flex flex-col gap-1 border-b p-3 last:border-b-0 sm:flex-row sm:items-start sm:justify-between"
                                            >
                                                <span className="text-sm font-medium">
                                                    {key.replaceAll("_", " ")}
                                                </span>

                                                <span className="break-all text-sm text-muted-foreground sm:text-right">
                                                    {String(value)}
                                                </span>
                                            </div>
                                        )
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}