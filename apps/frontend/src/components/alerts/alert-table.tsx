"use client";

import { useState } from "react";

import {
    useAlerts,
    useResolveAlert,
} from "@/hooks/use-alerts";

import { useCurrentUser } from "@/hooks/use-users";
import { canResolveAlerts } from "@/lib/permissions";

import type { AlertQueryParams } from "@/services/alerts.service";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import SeverityBadge from "./severity-badge";
import AlertDetails from "./alert-details";

const PAGE_SIZE = 20;

export default function AlertTable() {
    const { data: currentUser } = useCurrentUser();

    const [searchInput, setSearchInput] = useState("");
    const [search, setSearch] = useState("");

    const [status, setStatus] = useState("all");
    const [severity, setSeverity] = useState("");
    const [alertType, setAlertType] = useState("");

    const [startDate, setStartDate] = useState("");
    const [endDate, setEndDate] = useState("");

    const [sortOrder, setSortOrder] =
        useState<"asc" | "desc">("desc");

    const [page, setPage] = useState(0);

    const [selectedAlertId, setSelectedAlertId] =
        useState<number | null>(null);

    const [detailsOpen, setDetailsOpen] = useState(false);
    const [resolutionError, setResolutionError] =
        useState<string | null>(null);

    const [resolvingId, setResolvingId] =
        useState<number | null>(null);

    const invalidDateRange =
        Boolean(startDate && endDate) &&
        new Date(startDate).getTime() >
            new Date(endDate).getTime();

    const params: AlertQueryParams = {
        limit: PAGE_SIZE + 1,
        offset: page * PAGE_SIZE,
        sort_order: sortOrder,

        ...(search ? { search } : {}),
        ...(severity ? { severity } : {}),
        ...(alertType.trim()
            ? { alert_type: alertType.trim() }
            : {}),

        ...(status === "open"
            ? { resolved: false }
            : status === "resolved"
              ? { resolved: true }
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
    } = useAlerts(params, {
        enabled: !invalidDateRange,
    });

    const resolve = useResolveAlert();

    const alerts = data?.slice(0, PAGE_SIZE) ?? [];
    const hasNextPage = (data?.length ?? 0) > PAGE_SIZE;

    function resetFilters() {
        setSearchInput("");
        setSearch("");
        setStatus("all");
        setSeverity("");
        setAlertType("");
        setStartDate("");
        setEndDate("");
        setSortOrder("desc");
        setPage(0);
        setResolutionError(null);
    }

    async function handleResolve(id: number) {
        setResolutionError(null);
        setResolvingId(id);

        try {
            await resolve.mutateAsync(id);
        } catch {
            setResolutionError(
                `Failed to resolve alert #${id}. Please retry.`
            );
        } finally {
            setResolvingId(null);
        }
    }

    return (
        <div className="space-y-5">
            <div className="flex flex-wrap items-end gap-3 rounded-xl border bg-card p-4">
                <form
                    className="flex flex-wrap items-center gap-2"
                    onSubmit={(event) => {
                        event.preventDefault();
                        setSearch(searchInput.trim());
                        setPage(0);
                    }}
                >
                    <Input
                        placeholder="Search alerts..."
                        value={searchInput}
                        maxLength={200}
                        onChange={(event) =>
                            setSearchInput(event.target.value)
                        }
                        className="w-64"
                    />

                    <Button type="submit">
                        Search
                    </Button>
                </form>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="alert-status"
                        className="text-xs font-medium"
                    >
                        Status
                    </label>

                    <select
                        id="alert-status"
                        value={status}
                        onChange={(event) => {
                            setStatus(event.target.value);
                            setPage(0);
                        }}
                        className="h-9 rounded-md border bg-background px-3 text-sm"
                    >
                        <option value="all">All</option>
                        <option value="open">Open</option>
                        <option value="resolved">Resolved</option>
                    </select>
                </div>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="alert-severity"
                        className="text-xs font-medium"
                    >
                        Severity
                    </label>

                    <select
                        id="alert-severity"
                        value={severity}
                        onChange={(event) => {
                            setSeverity(event.target.value);
                            setPage(0);
                        }}
                        className="h-9 rounded-md border bg-background px-3 text-sm"
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
                        htmlFor="alert-type"
                        className="text-xs font-medium"
                    >
                        Alert Type
                    </label>

                    <Input
                        id="alert-type"
                        placeholder="Alert type"
                        value={alertType}
                        maxLength={100}
                        onChange={(event) => {
                            setAlertType(event.target.value);
                            setPage(0);
                        }}
                        className="w-40"
                    />
                </div>

                <div className="flex flex-col gap-1">
                    <label
                        htmlFor="alert-start-date"
                        className="text-xs font-medium"
                    >
                        Start Date
                    </label>

                    <Input
                        id="alert-start-date"
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
                        htmlFor="alert-end-date"
                        className="text-xs font-medium"
                    >
                        End Date
                    </label>

                    <Input
                        id="alert-end-date"
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
                        htmlFor="alert-sort"
                        className="text-xs font-medium"
                    >
                        Sort
                    </label>

                    <select
                        id="alert-sort"
                        value={sortOrder}
                        onChange={(event) => {
                            setSortOrder(
                                event.target.value as "asc" | "desc"
                            );
                            setPage(0);
                        }}
                        className="h-9 rounded-md border bg-background px-3 text-sm"
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
                    disabled={isFetching || invalidDateRange}
                >
                    {isFetching ? "Refreshing..." : "Refresh"}
                </Button>
            </div>

            {invalidDateRange && (
                <p
                    role="alert"
                    className="rounded-lg border border-red-200 p-3 text-sm text-red-600"
                >
                    Start date must be earlier than or equal to end date.
                </p>
            )}

            {resolutionError && (
                <p
                    role="alert"
                    className="rounded-lg border border-red-200 p-3 text-sm text-red-600"
                >
                    {resolutionError}
                </p>
            )}

            {invalidDateRange ? null : isLoading ? (
                <div className="rounded-xl border p-6">
                    Loading alerts...
                </div>
            ) : isError ? (
                <div className="rounded-xl border p-6">
                    <p className="text-red-600">
                        Failed to load alerts.
                    </p>

                    <Button
                        variant="outline"
                        className="mt-3"
                        onClick={() => refetch()}
                    >
                        Retry
                    </Button>
                </div>
            ) : alerts.length === 0 ? (
                <div className="rounded-xl border p-6">
                    <p className="font-semibold">
                        No matching alerts
                    </p>

                    <p className="mt-1 text-sm text-muted-foreground">
                        Try adjusting the filters.
                    </p>
                </div>
            ) : (
                <div className="overflow-x-auto rounded-xl border">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>ID</TableHead>
                                <TableHead>Severity</TableHead>
                                <TableHead>Type</TableHead>
                                <TableHead>Message</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Created</TableHead>
                                <TableHead>Action</TableHead>
                            </TableRow>
                        </TableHeader>

                        <TableBody>
                            {alerts.map((alert) => (
                                <TableRow
                                    key={alert.id}
                                    className="cursor-pointer"
                                    onClick={() => {
                                        setSelectedAlertId(alert.id);
                                        setDetailsOpen(true);
                                    }}
                                >
                                    <TableCell>{alert.id}</TableCell>

                                    <TableCell>
                                        <SeverityBadge
                                            severity={alert.severity}
                                        />
                                    </TableCell>

                                    <TableCell className="font-medium">
                                        {alert.alert_type}
                                    </TableCell>

                                    <TableCell className="max-w-xs truncate">
                                        {alert.message}
                                    </TableCell>

                                    <TableCell>
                                        {alert.resolved
                                            ? "Resolved"
                                            : "Open"}
                                    </TableCell>

                                    <TableCell>
                                        {new Date(
                                            alert.created_at
                                        ).toLocaleString()}
                                    </TableCell>

                                    <TableCell>
                                        {!alert.resolved &&
                                        canResolveAlerts(
                                            currentUser?.role
                                        ) ? (
                                            <Button
                                                size="sm"
                                                disabled={
                                                    resolve.isPending
                                                }
                                                onClick={(event) => {
                                                    event.stopPropagation();
                                                    void handleResolve(
                                                        alert.id
                                                    );
                                                }}
                                            >
                                                {resolvingId === alert.id
                                                    ? "Resolving..."
                                                    : "Resolve"}
                                            </Button>
                                        ) : (
                                            <span className="text-sm text-muted-foreground">
                                                —
                                            </span>
                                        )}
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

            <AlertDetails
                alertId={selectedAlertId}
                open={detailsOpen}
                onOpenChange={setDetailsOpen}
            />
        </div>
    );
}