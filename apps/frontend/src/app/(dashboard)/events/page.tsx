"use client";

import SecurityEventsTable from "@/components/events/security-events-table";

export default function EventsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
            Security Events
        </h1>

        <p className="mt-1 text-muted-foreground">
          Search, filter, and investigate security events
          recorded by the monitoring platform.
        </p>
      </div>

      <SecurityEventsTable />
    </div>
  );
}
