"use client";

import EventTable from "@/components/dashboard/event-table";

export default function EventsPage() {
    return (
        <div className="space-y-6">

            <div>
                <h1>
                    Security Events
                </h1>

                <p className="text-muted-foreground mt-1">
                    Search, inspect, and investigate security events in your system.
                </p>
            </div>
            <EventTable />
        </div>
    );
}