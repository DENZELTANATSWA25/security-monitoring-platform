"use client";

import { useState } from "react";

import { useEvents } from "@/hooks/use-events";
import EventDetails from "@/components/dashboard/event-details";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import type { SecurityEvent } from "@/types/event";
import type { EventQueryParams } from "@/services/events.service";

const PAGE_SIZE = 20;

export default function SecurityEventsTable() {
    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");

    const [severity, setSeverity] = useState("");
    const [eventType, setEventType] = useState("");
    const [source, setSource] = useState("");
    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");
    const [sortOrder, setSortOrder] =
        useState<"asc" | "desc">("desc");

    const [page, setPage] = useState(0);

    const [selectedEvent, setSelectedEvent] =
        useState<SecurityEvent | null>(null);

    const [dialogOpen, setDialogOpen] = useState(false);
    
    const hasInvalidDateRange =
        Boolean(startDate && endDate) &&
        new Date(startDate).getTime() > new Date(endDate).getTime();

    const params: EventQueryParams = {
        limit: PAGE_SIZE + 1,
        offset: page * PAGE_SIZE,
        sort_order: sortOrder,

        ...(search ? { search } : {}),
        ...(severity ? { severity } : {}),

        ...(eventType.trim()
            ? { event_type: eventType.trim() }
            : {}),

        ...(source.trim()
            ? { source: source.trim() }
            : {}),

        ...(startDate
            ? { start_date: new Date(startDate).toISOString() }
            : {}),

        ...(endDate
            ? { end_date: new Date(endDate).toISOString() }
            : {}),
    };

    const {
        data,
        isLoading,
        isError,
        isFetching,
        refetch,
    } = useEvents(params, {
        enabled: !hasInvalidDateRange,
    });

    const events = data?.slice(0, PAGE_SIZE) ?? [];
    const hasNextPage = (data?.length ?? 0) > PAGE_SIZE;

    function applySearch() {
        setPage(0);
        setSearch(searchInput.trim());
    }

    function resetFilters() {
        setSearchInput("");
        setSearch("");
        setSeverity("");
        setEventType("");
        setSource("");
        setStartDate("");
        setEndDate("");
        setSortOrder("desc");
        setPage(0);
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-wrap items-end gap-3 rounded-x1 border bg-card p-4">
                <form
                    className="flex flex-wrap items-center gap-2"
                    onSubmit={(event) => {
                        event.preventDefault();
                        applySearch();
                    }}
                >
                    <Input
                        placeholder="Search security events..."
                        value={searchInput}
                        maxLength={200}
                        onChange={(event) =>
                            setSearchInput(event.target.value)
                        }
                        className="w-72"
                    />

                    <Button type="submit">
                        Search
                    </Button>
                </form>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="event-type"
                        className="text-xs font-medium"
                    >
                        Event Type
                    </label>

                    <Input
                        id="event-type"
                        placeholder="e.g. SQL_INJECTION"
                        value={eventType}
                        maxLength={100}
                        onChange={(event) => {
                            setEventType(event.target.value);
                            setPage(0);
                        }}
                        className="w-44"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="event-source"
                        className="text-xs font-medium"
                    >
                        Source
                    </label>

                    <Input
                        id="event-source"
                        placeholder="e.g. web_application"
                        value={source}
                        maxLength={100}
                        onChange={(event) => {
                            setSource(event.target.value);
                            setPage(0);
                        }}
                        className="w-44"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="event-start-date"
                        className="text-xs font-medium"
                    >
                        Start Date
                    </label>

                    <Input
                        id="event-start-date"
                        type="datetime-local"
                        value={startDate}
                        onChange={(event) => {
                            setStartDate(event.target.value);
                            setPage(0);
                        }}
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="event-end-date"
                        className="text-xs font-medium"
                    >
                        End Date
                    </label>

                    <Input
                        id="event-end-date"
                        type="datetime-local"
                        value={endDate}
                        onChange={(event) => {
                            setEndDate(event.target.value);
                            setPage(0);
                        }}
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="event-severity"
                        className="text-xs font-medium"
                    >
                        Severity
                    </label>

                    <select
                        id="event-severity"
                        value={severity}
                        onChange={(event) => {
                            setSeverity(event.target.value);
                            setPage(0);
                        }}
                        className="h-9 rounded-md border bg-white px-3 text-sm"
                    >
                        <option value="">All severities</option>
                        <option value="INFO">Info</option>
                        <option value="WARNING">Warning</option>
                        <option value="ERROR">Error</option>
                        <option value="CRITICAL">Critical</option>
                    </select>
                </div>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="event-sort"
                        className="text-xs font-medium"
                    >
                        Sort
                    </label>

                    <select
                        id="event-sort"
                        value={sortOrder}
                        onChange={(event) => {
                            setSortOrder(
                                event.target.value as "asc" | "desc"
                            );
                            setPage(0);
                        }}
                        className="h-9 rounded-md border bg-white px-3 text-sm"
                    >
                        <option value="desc">Newest first</option>
                        <option value="asc">Oldest first</option>
                    </select>
                </div>

                <Button
                    variant="outline"
                    onClick={resetFilters}
                >
                    Reset
                </Button>

                <Button
                    variant="outline"
                    onClick={() => refetch()}
                    disabled={isFetching}
                >
                    {isFetching ? "Refreshing..." : "Refresh"}
                </Button>
            </div>

            {hasInvalidDateRange ? (
                <div
                    role="alert"
                    className="rounded-xl border border-red-200 p-6"
                >
                    <p className="text-red-600">
                        Start date must be earlier than or equal to end date.
                    </p>
                </div>
            ) : isLoading ? (
                <p>Loading security events...</p>
            ) : isError ? (
                <div className="rounded-xl border p-6">
                    <p className="text-red-600">
                        Failed to load security events.
                    </p>
                    <Button
                        variant="outline"
                        className="mt-3"
                        onClick={() => refetch()}
                    >
                        Retry
                    </Button>
                </div>
            ) : events.length === 0 ? (
                <div className="rounded-xl border p-6">
                    <p className="font-semibold">
                        No security events found
                    </p>

                    <p className="mt-1 text-sm text-muted-foreground">
                        Try changing your search or filters.
                    </p>
                </div>
            ) : (
                <div className="overflow-x-auto rounded-xl border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>ID</TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead>Severity</TableHead>
                                <TableHead>Source</TableHead>
                                <TableHead>Message</TableHead>
                                <TableHead>Created</TableHead>
                            </TableRow>
                        </TableHeader>

                        <TableBody>
                            {events.map((event) => (
                                <TableRow
                                    key={event.id}
                                    className="cursor-pointer"
                                    onClick={() => {
                                        setSelectedEvent(event);
                                        setDialogOpen(true);
                                    }}
                                >
                                    <TableCell>{event.id}</TableCell>

                                    <TableCell>
                                        {event.event_type}
                                    </TableCell>

                                    <TableCell>
                                        <Badge
                                            variant={
                                                event.severity === "CRITICAL"
                                                    ? "destructive"
                                                    : "outline"
                                            }
                                        >
                                            {event.severity}
                                        </Badge>
                                    </TableCell>

                                    <TableCell>{event.source}</TableCell>

                                    <TableCell className="max-w-xs truncate">
                                        {event.message}
                                    </TableCell>

                                    <TableCell>
                                        {new Date(
                                            event.created_at
                                        ).toLocaleString()}
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>
            )}

            <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                    Page {page + 1}
                </p>

                <div className="flex gap-2">
                    <Button
                        variant="outline"
                        disabled={page === 0 || isFetching}
                        onClick={() =>
                            setPage((previous) =>
                                Math.max(0, previous - 1)
                            )
                        }
                    >
                        Previous
                    </Button>

                    <Button
                        variant="outline"
                        disabled={!hasNextPage || isFetching}
                        onClick={() =>
                            setPage((previous) => previous + 1)
                        }
                    >
                        Next
                    </Button>
                </div>
            </div>

            <EventDetails
                event={selectedEvent}
                open={dialogOpen}
                onOpenChange={setDialogOpen}
            />
        </div>
    );
}