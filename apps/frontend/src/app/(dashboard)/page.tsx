"use client";

import Link from "next/link";

import {
  ArrowUpRight,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";

import { useDashboard } from "@/hooks/use-dashboard";
import { useLiveEvents } from "@/hooks/use-live-events";

import DashboardGrid from "@/components/dashboard/dashboard-grid";
import EventChart from "@/components/dashboard/event-chart";
import EventsTable from "@/components/dashboard/event-table";
import AlertsPanel from "@/components/dashboard/alerts-panel";

export default function Home() {
  const {
    data,
    isLoading,
    isError,
    refetch,
    isFetching,
  } = useDashboard();

  useLiveEvents();

  if (isLoading) {
    return (
      <div className="space-y-6" role="status">
        <div className="h-10 w-64 animate-pulse rounded-lg bg-muted" />

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div
              key={index}
              className="h-36 animate-pulse rounded-xl bg-muted"
            />
          ))}
        </div>

        <div className="h-80 animate-pulse rounded-xl bg-muted" />

        <span className="sr-only">
          Loading security dashboard
        </span>
      </div>
    );
  }

  if (isError) {
    return (
      <div
        role="alert"
        className="
          rounded-xl border border-destructive/30
          bg-destructive/5 p-8
        "
      >
        <h1 className="text-xl font-semibold">
          Dashboard unavailable
        </h1>

        <p className="mt-2 text-sm text-muted-foreground">
          Security metrics could not be loaded.
          Check your connection and try again.
        </p>

        <Button
          className="mt-5"
          variant="outline"
          onClick={() => refetch()}
        >
          <RefreshCw className="mr-2 size-4" />
          Retry
        </Button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border bg-card p-8">
        <h1 className="text-xl font-semibold">
          No dashboard data available
        </h1>

        <p className="mt-2 text-sm text-muted-foreground">
          The dashboard has not returned any metrics.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Page heading */}
      <div
        className="
          flex flex-col gap-4
          sm:flex-row sm:items-start sm:justify-between
        "
      >
        <div>
          <div className="mb-3 flex items-center gap-2">
            <ShieldCheck
              aria-hidden="true"
              className="size-4 text-primary"
            />

            <span
              className="
                text-xs font-semibold uppercase
                tracking-[0.12em] text-muted-foreground
              "
            >
              Security Operations
            </span>
          </div>

          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Security Dashboard
          </h1>

          <p className="mt-2 text-sm text-muted-foreground">
            Monitor security activity, review alerts,
            and investigate suspicious events.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            disabled={isFetching}
            onClick={() => refetch()}
          >
            <RefreshCw
              className={`mr-2 size-4 ${
                isFetching ? "animate-spin" : ""
              }`}
            />
            Refresh
          </Button>

          <Link
            href="/incidents"
            className="
              inline-flex h-9 items-center justify-center gap-2
              rounded-md bg-primary px-4 text-sm font-medium
              text-primary-foreground
              transition-colors hover:bg-primary/90
              focus-visible:outline-2 focus-visible:outline-ring
              "
            >
              View Incidents
              <ArrowUpRight className="size-4" />
            </Link>

        </div>
      </div>

      {/* Metrics */}
      <DashboardGrid data={data} />

      {/* Event activity */}
      <EventChart />

      {/* Investigation workspace */}
      <div className="space-y-8">
        <EventsTable />
        <AlertsPanel />
      </div>
    </div>
  );
}