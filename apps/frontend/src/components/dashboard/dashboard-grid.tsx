"use client";

import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  LockKeyhole,
  ShieldAlert,
  UserRoundCheck,
} from "lucide-react";

import StatCard from "./stat-card";

import type { DashboardSummary } from "@/types/dashboard";

type DashboardGridProps = {
  data: DashboardSummary;
};

export default function DashboardGrid({
  data,
}: DashboardGridProps) {
  return (
    <section aria-labelledby="security-metrics-heading">
      <div className="mb-5">
        <h2
          id="security-metrics-heading"
          className="text-lg font-semibold tracking-tight"
        >
          Security Overview
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          Current security activity and authentication metrics.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard
          title="Active Alerts"
          value={data.active_alerts}
          icon={<ShieldAlert className="size-5" />}
          description="Unresolved security alerts"
          priority="critical"
          href="/alerts"
        />

        <StatCard
          title="Critical Events"
          value={data.critical_events}
          icon={<AlertTriangle className="size-5" />}
          description="Events classified as critical"
          priority="warning"
          href="/events"
        />

        <StatCard
          title="Total Events"
          value={data.total_events}
          icon={<Activity className="size-5" />}
          description="Recorded security events"
          href="/events"
        />

        <StatCard
          title="Resolved Alerts"
          value={data.resolved_alerts}
          icon={<CheckCircle2 className="size-5" />}
          description="Alerts marked as resolved"
          priority="success"
          href="/alerts"
        />

        <StatCard
          title="Failed Logins (24h)"
          value={data.failed_logins_24h}
          icon={<LockKeyhole className="size-5" />}
          description="Failed authentication attempts"
          priority="warning"
          href="/events"
        />

        <StatCard
          title="Successful Logins (24h)"
          value={data.successful_logins_24h}
          icon={<UserRoundCheck className="size-5" />}
          description="Successful authentication attempts"
          href="/events"
        />
      </div>
    </section>
  );
}