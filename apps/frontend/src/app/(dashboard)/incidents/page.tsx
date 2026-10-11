"use client";

import Link from "next/link";
import { useState } from "react";

import { useIncidents } from "@/hooks/use-incidents";
import type { IncidentStatus } from "@/types/incident";
import type { IncidentQueryParams } from "@/services/incident.service";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const PAGE_SIZE = 10;

type StatusFilter = IncidentStatus | "";

type AssignmentFilter =
  | "all"
  | "assigned"
  | "unassigned";

interface Filters {
  search: string;
  status: StatusFilter;
  severity: string;
  assignment: AssignmentFilter;
  startDate: string;
  endDate: string;
  sortOrder: "asc" | "desc";
}

const DEFAULT_FILTERS: Filters = {
  search: "",
  status: "",
  severity: "",
  assignment: "all",
  startDate: "",
  endDate: "",
  sortOrder: "desc",
};

export default function IncidentsPage() {
  const [draftSearch, setDraftSearch] = useState("");

  const [filters, setFilters] =
    useState<Filters>(DEFAULT_FILTERS);

  const [page, setPage] = useState(1);

  const [assignedUserId, setAssignedUserId] =
    useState("");

  const offset = (page - 1) * PAGE_SIZE;

  const assignmentId = Number(assignedUserId);

  const invalidAssignment =
    filters.assignment === "assigned" &&
    (
        assignedUserId.trim() === "" ||
        !Number.isInteger(assignmentId) ||
        assignmentId <= 0
    );

  const queryParams: IncidentQueryParams = {
    limit: PAGE_SIZE + 1,
    offset,
    sort_order: filters.sortOrder,
  };

  if (filters.search) {
    queryParams.search = filters.search;
  }

  if (filters.status) {
    queryParams.status = filters.status;
  }

  if (filters.severity) {
    queryParams.severity = filters.severity;
  }

  if (
    filters.assignment === "unassigned" &&
    !invalidAssignment
    ) {
        queryParams.assigned_user_id = assignmentId;
    }

  if (filters.assignment === "assigned") {
    const userId = Number(assignedUserId);

    if (
        assignedUserId.trim() !== "" &&
        Number.isInteger(userId) &&
        userId > 0
    ) {
      queryParams.assigned_user_id = userId;
    }
}

  if (filters.startDate) {
    queryParams.start_date = new Date(
      `${filters.startDate}T00:00:00`,
    ).toISOString();
  }

  if (filters.endDate) {
    queryParams.end_date = new Date(
      `${filters.endDate}T23:59:59`,
    ).toISOString();
  }

  const {
    data = [],
    isLoading,
    isFetching,
    error,
    refetch,
  } = useIncidents(queryParams);

  const incidents = data.slice(0, PAGE_SIZE);
  const hasNextPage = data.length > PAGE_SIZE;

  function updateFilters(
    changes: Partial<Filters>,
  ) {
    setFilters((previous) => ({
      ...previous,
      ...changes,
    }));

    setPage(1);
  }

  function handleSearch(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    updateFilters({
      search: draftSearch.trim(),
    });
  }

  function resetFilters() {
    setFilters(DEFAULT_FILTERS);
    setDraftSearch("");
    setAssignedUserId("");
    setPage(1);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
          Security Incidents
        </h1>

        <p className="mt-1 text-muted-foreground">
          Investigate and manage security incidents.
        </p>
      </div>

      {/* Filters */}

      <Card>
        <CardContent className="space-y-4 pt-6">
          <form
            onSubmit={handleSearch}
            className="flex flex-wrap gap-2"
          >
            <Input
              value={draftSearch}
              onChange={(event) =>
                setDraftSearch(event.target.value)
              }
              placeholder="Search incidents..."
              maxLength={200}
              className="w-full sm:max-w-sm"
            />

            <Button type="submit">
              Search
            </Button>
          </form>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="space-y-1 text-sm">
              <span>Status</span>

              <select
                value={filters.status}
                onChange={(event) =>
                  updateFilters({
                    status:
                      event.target.value as StatusFilter,
                  })
                }
                className="h-9 w-full rounded-md border px-3"
              >
                <option value="">All statuses</option>
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">
                  In progress
                </option>
                <option value="RESOLVED">
                  Resolved
                </option>
                <option value="CLOSED">Closed</option>
              </select>
            </label>

            <label className="space-y-1 text-sm">
              <span>Severity</span>

              <select
                value={filters.severity}
                onChange={(event) =>
                  updateFilters({
                    severity: event.target.value,
                  })
                }
                className="h-9 w-full rounded-md border px-3"
              >
                <option value="">All severities</option>
                <option value="CRITICAL">
                  Critical
                </option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </label>

            <label className="space-y-1 text-sm">
              <span>Assignment</span>

              <select
                value={filters.assignment}
                onChange={(event) =>
                  updateFilters({
                    assignment:
                      event.target.value as AssignmentFilter,
                  })
                }
                className="h-9 w-full rounded-md border px-3"
              >
                <option value="all">
                  All incidents
                </option>
                <option value="unassigned">
                  Unassigned
                </option>
                <option value="assigned">
                  Assigned to user ID
                </option>
              </select>
            </label>

            <label className="space-y-1 text-sm">
              <span>Sort</span>

              <select
                value={filters.sortOrder}
                onChange={(event) =>
                  updateFilters({
                    sortOrder:
                      event.target.value as
                        | "asc"
                        | "desc",
                  })
                }
                className="h-9 w-full rounded-md border px-3"
              >
                <option value="desc">
                  Newest first
                </option>
                <option value="asc">
                  Oldest first
                </option>
              </select>
            </label>

            {filters.assignment === "assigned" && (
              <label className="space-y-1 text-sm">
                <span>Assigned user ID</span>

                <Input
                  type="number"
                  min={1}
                  value={assignedUserId}
                  onChange={(event) => {
                    setAssignedUserId(
                      event.target.value,
                    );
                    setPage(1);
                  }}
                  placeholder="Enter user ID"
                />
              </label>
            )}

            <label className="space-y-1 text-sm">
              <span>Start date</span>

              <Input
                type="date"
                value={filters.startDate}
                onChange={(event) =>
                  updateFilters({
                    startDate: event.target.value,
                  })
                }
              />
            </label>

            <label className="space-y-1 text-sm">
              <span>End date</span>

              <Input
                type="date"
                value={filters.endDate}
                min={filters.startDate || undefined}
                onChange={(event) =>
                  updateFilters({
                    endDate: event.target.value,
                  })
                }
              />
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={resetFilters}
            >
              Reset
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              {isFetching
                ? "Refreshing..."
                : "Refresh"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {filters.assignment === "assigned" &&
        !assignedUserId.trim() && (
            <p className="text-sm text-muted-foreground">
                Enter a user ID to filter incidents by assignee.
            </p>
        )}

      {/* Results */}
      {invalidAssignment ? (
        <Card>
            <CardContent className="p-8 text-center">
                Enter a valid positive user ID to filter incidents.
            </CardContent>
        </Card>
      ) : isLoading ? (
        <Card>
          <CardContent className="p-8">
            Loading incidents...
          </CardContent>
        </Card>
      ) : error ? (
        <Card>
          <CardContent className="p-8 text-destructive">
            Failed to load incidents.
          </CardContent>
        </Card>
      ) : incidents.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            No matching incidents found.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {incidents.map((incident) => (
            <Link
              key={incident.id}
              href={`/incidents/${incident.id}`}
            >
              <Card className="transition-colors duration-200 hover:bg-accent/40 hover:border-primary/30">
                <CardHeader>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <CardTitle>
                      {incident.title}
                    </CardTitle>

                    <Badge>
                      {incident.status.replaceAll(
                        "_",
                        " ",
                      )}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <p className="text-sm text-muted-foreground">
                        Severity
                      </p>

                      <p className="font-semibold">
                        {incident.severity}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">
                        Assigned To
                      </p>

                      <p className="font-semibold">
                        {incident.assigned_to ??
                          "Unassigned"}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">
                        Event
                      </p>

                      <p className="font-semibold">
                        {incident.event_id
                          ? `Event #${incident.event_id}`
                          : "None"}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm text-muted-foreground">
                        Created
                      </p>

                      <p className="font-semibold">
                        {new Date(
                          incident.created_at,
                        ).toLocaleString()}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Page {page}
        </p>

        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={page === 1 || isFetching}
            onClick={() =>
              setPage((previous) =>
                Math.max(1, previous - 1),
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
    </div>
  );
}