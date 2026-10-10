"use client";

import { useState } from "react";
import axios from "axios";

import { useCurrentUser } from "@/hooks/use-users";
import { useAuditLogs } from "@/hooks/use-audit-logs";

import { canViewAuditLogs } from "@/lib/permissions";

import type {
    AuditLogFilters,
    AuditSortOrder,
} from "@/types/audit";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";


const PAGE_SIZE = 25;


type FilterForm = {
    userId: string;
    action: string;
    resource: string;
    search: string;
    startDate: string;
    endDate: string;
    sortOrder: AuditSortOrder;
};


const EMPTY_FILTERS: FilterForm = {
    userId: "",
    action: "",
    resource: "",
    search: "",
    startDate: "",
    endDate: "",
    sortOrder: "desc",
};


function getErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
            return detail;
        }

        return error.message;
    }

    if (error instanceof Error) {
        return error.message;
    }

    return "An unexpected error occurred.";
}


function formatTimestamp(value: string): string {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Unknown";
    }

    return date.toLocaleString();
}


function toDateParameter(
    value: string,
    endOfDay = false
): string | undefined {
    if (!value) {
        return undefined;
    }

    const date = new Date(
        `${value}T${endOfDay ? "23:59:59.999" : "00:00:00.000"}`
    );

    return date.toISOString();
}


function buildFilters(
    form: FilterForm,
    page: number
): AuditLogFilters {
    return {
        limit: PAGE_SIZE + 1,
        offset: page * PAGE_SIZE,

        user_id: form.userId
            ? Number(form.userId)
            : undefined,

        action: form.action.trim() || undefined,
        resource: form.resource.trim() || undefined,
        search: form.search.trim() || undefined,

        start_date: toDateParameter(form.startDate),
        end_date: toDateParameter(form.endDate, true),

        sort_order: form.sortOrder,
    };
}


export default function AuditLogsPage() {
    const {
        data: currentUser,
        isPending: isPendingCurrentUser,
        error: currentUserError,
    } = useCurrentUser();

    const canView = canViewAuditLogs(currentUser?.role);

    const [draftFilters, setDraftFilters] =
        useState<FilterForm>({ ...EMPTY_FILTERS });

    const [appliedFilters, setAppliedFilters] =
        useState<FilterForm>({ ...EMPTY_FILTERS });

    const [page, setPage] = useState(0);

    const filters = buildFilters(appliedFilters, page);

    const {
        data = [],
        isLoading,
        isFetching,
        error,
        refetch,
    } = useAuditLogs(
        filters,
        canView
    );

    const logs = data.slice(0, PAGE_SIZE);

    const hasNextPage = data.length > PAGE_SIZE;
    const hasPreviousPage = page > 0;


    function applyFilters() {
        if (
            draftFilters.startDate &&
            draftFilters.endDate &&
            draftFilters.startDate > draftFilters.endDate
        ) {
            return;
        }

        setPage(0);
        setAppliedFilters({ ...draftFilters });
    }


    function resetFilters() {
        setDraftFilters({ ...EMPTY_FILTERS });
        setAppliedFilters({ ...EMPTY_FILTERS });
        setPage(0);
    }


    if (isPendingCurrentUser) {
        return (
            <div className="p-6">
                Loading account permissions...
            </div>
        );
    }


    if (currentUserError) {
        return (
            <div className="p-6 space-y-2">
                <h1 className="text-2xl font-bold">
                    Unable to verify permissions
                </h1>

                <p className="text-muted-foreground">
                    {getErrorMessage(currentUserError)}
                </p>
            </div>
        );
    }


    if (!canView) {
        return (
            <div className="p-6 space-y-2">
                <h1 className="text-2xl font-bold">
                    Access Denied
                </h1>

                <p className="text-muted-foreground">
                    Only administrators can view audit logs.
                </p>
            </div>
        );
    }


    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">
                    Audit Logs
                </h1>

                <p className="mt-1 text-muted-foreground">
                    Investigate administrative actions and
                    security-related activity.
                </p>
            </div>


            <Card>
                <CardHeader>
                    <CardTitle>
                        Filters
                    </CardTitle>
                </CardHeader>

                <CardContent>
                    <form
                        className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"
                        onSubmit={(event) => {
                            event.preventDefault();
                            applyFilters();
                        }}
                    >
                        <label className="space-y-1 text-sm">
                            <span>Search</span>

                            <input
                                type="search"
                                maxLength={200}
                                value={draftFilters.search}
                                onChange={(event) =>
                                    setDraftFilters({
                                        ...draftFilters,
                                        search: event.target.value,
                                    })
                                }
                                placeholder="Search audit details"
                                className="h-10 w-full rounded-md border bg-background px-3"
                            />
                        </label>


                        <label className="space-y-1 text-sm">
                            <span>User ID</span>

                            <input
                                type="number"
                                min={1}
                                value={draftFilters.userId}
                                onChange={(event) =>
                                    setDraftFilters({
                                        ...draftFilters,
                                        userId: event.target.value,
                                    })
                                }
                                placeholder="e.g. 2"
                                className="h-10 w-full rounded-md border bg-background px-3"
                            />
                        </label>


                        <label className="space-y-1 text-sm">
                            <span>Action</span>

                            <input
                                type="text"
                                maxLength={100}
                                value={draftFilters.action}
                                onChange={(event) =>
                                    setDraftFilters({
                                        ...draftFilters,
                                        action: event.target.value,
                                    })
                                }
                                placeholder="e.g. USER_ROLE_CHANGED"
                                className="h-10 w-full rounded-md border bg-background px-3"
                            />
                        </label>


                        <label className="space-y-1 text-sm">
                            <span>Resource</span>

                            <input
                                type="text"
                                maxLength={200}
                                value={draftFilters.resource}
                                onChange={(event) =>
                                    setDraftFilters({
                                        ...draftFilters,
                                        resource: event.target.value,
                                    })
                                }
                                placeholder="e.g. USER"
                                className="h-10 w-full rounded-md border bg-background px-3"
                            />
                        </label>


                        <label className="space-y-1 text-sm">
                            <span>Start date</span>

                            <input
                                type="date"
                                value={draftFilters.startDate}
                                onChange={(event) =>
                                    setDraftFilters({
                                        ...draftFilters,
                                        startDate: event.target.value,
                                    })
                                }
                                className="h-10 w-full rounded-md border bg-background px-3"
                            />
                        </label>


                        <label className="space-y-1 text-sm">
                            <span>End date</span>

                            <input
                                type="date"
                                value={draftFilters.endDate}
                                onChange={(event) =>
                                    setDraftFilters({
                                        ...draftFilters,
                                        endDate: event.target.value,
                                    })
                                }
                                className="h-10 w-full rounded-md border bg-background px-3"
                            />
                        </label>


                        <label className="space-y-1 text-sm">
                            <span>Sort order</span>

                            <select
                                value={draftFilters.sortOrder}
                                onChange={(event) =>
                                    setDraftFilters({
                                        ...draftFilters,
                                        sortOrder:
                                            event.target.value as AuditSortOrder,
                                    })
                                }
                                className="h-10 w-full rounded-md border bg-background px-3"
                            >
                                <option value="desc">
                                    Newest first
                                </option>

                                <option value="asc">
                                    Oldest first
                                </option>
                            </select>
                        </label>


                        <div className="flex items-end gap-2">
                            <Button type="submit">
                                Apply Filters
                            </Button>

                            <Button
                                type="button"
                                variant="outline"
                                onClick={resetFilters}
                            >
                                Reset
                            </Button>
                        </div>
                    </form>

                    {draftFilters.startDate &&
                        draftFilters.endDate &&
                        draftFilters.startDate >
                            draftFilters.endDate && (
                            <p
                                role="alert"
                                className="mt-3 text-sm text-red-600"
                            >
                                Start date cannot be after end date.
                            </p>
                        )}
                </CardContent>
            </Card>


            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between gap-3">
                        <CardTitle>
                            Audit Events
                        </CardTitle>

                        <Button
                            variant="outline"
                            size="sm"
                            disabled={isFetching}
                            onClick={() => void refetch()}
                        >
                            Refresh
                        </Button>
                    </div>
                </CardHeader>


                <CardContent>
                    {isLoading ? (
                        <p className="py-8 text-center text-muted-foreground">
                            Loading audit logs...
                        </p>
                    ) : error ? (
                        <div className="space-y-3 py-6">
                            <p className="font-medium text-red-600">
                                Failed to load audit logs.
                            </p>

                            <p className="text-sm text-muted-foreground">
                                {getErrorMessage(error)}
                            </p>

                            <Button
                                variant="outline"
                                onClick={() => void refetch()}
                            >
                                Try Again
                            </Button>
                        </div>
                    ) : logs.length === 0 ? (
                        <p className="py-8 text-center text-muted-foreground">
                            No audit events match the selected filters.
                        </p>
                    ) : (
                        <div className="overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Timestamp</TableHead>
                                        <TableHead>Action</TableHead>
                                        <TableHead>Resource</TableHead>
                                        <TableHead>User ID</TableHead>
                                        <TableHead>Details</TableHead>
                                    </TableRow>
                                </TableHeader>

                                <TableBody>
                                    {logs.map((log) => (
                                        <TableRow key={log.id}>
                                            <TableCell className="whitespace-nowrap">
                                                {formatTimestamp(log.timestamp)}
                                            </TableCell>

                                            <TableCell>
                                                <Badge variant="secondary">
                                                    {log.action}
                                                </Badge>
                                            </TableCell>

                                            <TableCell>
                                                {log.resource ?? "—"}
                                            </TableCell>

                                            <TableCell>
                                                {log.user_id ?? "System"}
                                            </TableCell>

                                            <TableCell className="max-w-md break-words">
                                                {log.details ?? "—"}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    )}


                    <div className="mt-5 flex items-center justify-between">
                        <p className="text-sm text-muted-foreground">
                            Page {page + 1}
                        </p>

                        <div className="flex gap-2">
                            <Button
                                variant="outline"
                                disabled={
                                    !hasPreviousPage ||
                                    isFetching
                                }
                                onClick={() =>
                                    setPage((current) => current - 1)
                                }
                            >
                                Previous
                            </Button>

                            <Button
                                variant="outline"
                                disabled={
                                    !hasNextPage ||
                                    isFetching
                                }
                                onClick={() =>
                                    setPage((current) => current + 1)
                                }
                            >
                                Next
                            </Button>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}