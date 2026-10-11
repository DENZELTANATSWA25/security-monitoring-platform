"use client";

import { useState } from "react";
import Link from "next/link";

import {
    ArrowUpRight,
    ChevronRight,
    Database,
    RefreshCw,
    Search,
    ShieldAlert,
} from "lucide-react";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

import { useEvents } from "@/hooks/use-events";
import type { SecurityEvent } from "@/types/event";

import EventDetails from "./event-details";

const SEVERITY_STYLES: Record<
    SecurityEvent["severity"],
    string
> = {
    CRITICAL:
        "border-red-500/30 bg-red-500/10 text-red-500 dark:text-red-400",
    ERROR:
        "border-orange-500/30 bg-orange-500/10 text-orange-600 dark:text-orange-400",
    WARNING:
        "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400",
    INFO:
        "border-blue-500/30 bg-blue-500/10 text-blue-600 dark:text-blue-400",
};

function formatTimestamp(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(date);
}

export default function EventsTable() {
    const {
        data,
        isLoading,
        isError,
        isFetching,
        refetch,
    } = useEvents();

    const [search, setSearch] = useState("");

    const [selectedEvent, setSelectedEvent] =
        useState<SecurityEvent | null>(null);

    const [dialogOpen, setDialogOpen] =
        useState(false);

    const normalizedSearch = search.trim().toLowerCase();

    const filteredEvents =
        data?.filter((event) => {
            if (!normalizedSearch) {
                return true;
            }

            return [
                String(event.id),
                event.event_type,
                event.severity,
                event.source,
                event.message,
            ].some((value) =>
                value.toLowerCase().includes(normalizedSearch)
            );
        }) ?? [];

    const displayedEvents = filteredEvents.slice(0, 10);

    function openInvestigation(event: SecurityEvent) {
        setSelectedEvent(event);
        setDialogOpen(true);
    }

    return (
        <>
            <Card className="overflow-hidden border-border/70 bg-card shadow-sm">
                <CardHeader className="gap-4 border-b border-border/60 pb-5 lg:flex-row lg:items-center lg:justify-between">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                                <Database
                                    className="size-4"
                                    aria-hidden="true"
                                />
                            </div>

                            <div>
                                <CardTitle className="text-base font-semibold tracking-tight">
                                    Recent Security Events
                                </CardTitle>

                                <p className="mt-1 text-xs text-muted-foreground">
                                    Latest recorded activity across monitored sources
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                        <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            disabled={isFetching}
                            onClick={() => void refetch()}
                            className="gap-2"
                            aria-label="Refresh recent security events"
                        >
                            <RefreshCw
                                className={`size-3.5 ${
                                    isFetching ? "animate-spin" : ""
                                }`}
                                aria-hidden="true"
                            />

                            Refresh
                        </Button>

                        <Link
                            href="/events"
                            className="inline-flex h-8 items-center justify-center gap-2 rounded-md border border-input bg-background px-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                        >
                            View all events

                            <ArrowUpRight
                                className="size-3.5"
                                aria-hidden="true"
                            />
                        </Link>


                    </div>
                </CardHeader>

                <CardContent className="space-y-5 pt-5">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                        <div className="relative w-full sm:max-w-sm">
                            <Search
                                className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                                aria-hidden="true"
                            />

                            <Input
                                type="search"
                                aria-label="Search recent security events"
                                placeholder="Search events, sources, severity..."
                                value={search}
                                onChange={(event) =>
                                    setSearch(event.target.value)
                                }
                                className="pl-9"
                            />
                        </div>

                        <p className="text-xs text-muted-foreground">
                            {isLoading
                                ? "Loading events..."
                                : `${filteredEvents.length} matching events`}
                        </p>
                    </div>

                    {isLoading ? (
                        <div
                            className="space-y-3"
                            role="status"
                            aria-live="polite"
                        >
                            {Array.from({ length: 5 }).map((_, index) => (
                                <div
                                    key={index}
                                    className="h-12 animate-pulse rounded-lg bg-muted/50"
                                />
                            ))}

                            <span className="sr-only">
                                Loading security events
                            </span>
                        </div>
                    ) : isError ? (
                        <div
                            role="alert"
                            className="flex flex-col items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 px-6 py-12 text-center"
                        >
                            <ShieldAlert
                                className="size-8 text-destructive"
                                aria-hidden="true"
                            />

                            <h3 className="font-semibold">
                                Unable to load security events
                            </h3>

                            <p className="max-w-sm text-sm text-muted-foreground">
                                Recent security activity could not be retrieved.
                            </p>

                            <Button
                                type="button"
                                variant="outline"
                                onClick={() => void refetch()}
                            >
                                Try again
                            </Button>
                        </div>
                    ) : filteredEvents.length === 0 ? (
                        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border px-6 py-12 text-center">
                            <Database
                                className="size-8 text-muted-foreground"
                                aria-hidden="true"
                            />

                            <h3 className="font-semibold">
                                {search.trim()
                                    ? "No matching events"
                                    : "No security events recorded"}
                            </h3>

                            <p className="max-w-sm text-sm text-muted-foreground">
                                {search.trim()
                                    ? "Try adjusting your search terms."
                                    : "New security events will appear here as telemetry is received."}
                            </p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto rounded-xl border border-border/70">
                            <Table className="min-w-[850px]">
                                <TableHeader className="bg-muted/40">
                                    <TableRow className="hover:bg-transparent">
                                        <TableHead className="w-16">
                                            ID
                                        </TableHead>

                                        <TableHead>
                                            Event Type
                                        </TableHead>

                                        <TableHead>
                                            Severity
                                        </TableHead>

                                        <TableHead>
                                            Source
                                        </TableHead>

                                        <TableHead>
                                            Detected
                                        </TableHead>

                                        <TableHead className="w-20 text-right">
                                            Action
                                        </TableHead>
                                    </TableRow>
                                </TableHeader>

                                <TableBody>
                                    {displayedEvents.map((event) => (
                                        <TableRow
                                            key={event.id}
                                            className="transition-colors hover:bg-muted/40"
                                        >
                                            <TableCell className="font-mono text-xs text-muted-foreground">
                                                #{event.id}
                                            </TableCell>

                                            <TableCell>
                                                <div className="max-w-[260px] space-y-1">
                                                    <p
                                                        className="truncate text-sm font-medium"
                                                        title={event.event_type}
                                                    >
                                                        {event.event_type}
                                                    </p>

                                                    <p
                                                        className="truncate text-xs text-muted-foreground"
                                                        title={event.message}
                                                    >
                                                        {event.message}
                                                    </p>
                                                </div>
                                            </TableCell>

                                            <TableCell>
                                                <span
                                                    className={`inline-flex rounded-md border px-2 py-1 text-[10px] font-semibold tracking-wide ${
                                                        SEVERITY_STYLES[event.severity]
                                                    }`}
                                                >
                                                    {event.severity}
                                                </span>
                                            </TableCell>

                                            <TableCell>
                                                <span
                                                    className="block max-w-[170px] truncate text-xs text-muted-foreground"
                                                    title={event.source}
                                                >
                                                    {event.source}
                                                </span>
                                            </TableCell>

                                            <TableCell className="whitespace-nowrap text-xs text-muted-foreground">
                                                {formatTimestamp(
                                                    event.created_at
                                                )}
                                            </TableCell>

                                            <TableCell className="text-right">
                                                <Button
                                                    type="button"
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={() =>
                                                        openInvestigation(event)
                                                    }
                                                    aria-label={`Investigate event ${event.id}`}
                                                    title="Investigate event"
                                                >
                                                    <ChevronRight
                                                        className="size-4"
                                                        aria-hidden="true"
                                                    />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}

                    {!isLoading &&
                        !isError &&
                        filteredEvents.length > 10 && (
                            <p className="text-xs text-muted-foreground">
                                Showing the first 10 matching events.
                                Use View all events for the complete event list.
                            </p>
                        )}
                </CardContent>
            </Card>

            <EventDetails
                event={selectedEvent}
                open={dialogOpen}
                onOpenChange={setDialogOpen}
            />
        </>
    );
}