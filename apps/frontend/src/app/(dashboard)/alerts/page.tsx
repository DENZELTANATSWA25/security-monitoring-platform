"use client"

import AlertTable from "@/components/alerts/alert-table";

export default function AlertsPage() {
    return (
        <div className="space-y-6">

            <div>
                <h1 className="text-3x1 font-bold">
                    Security Alerts
                </h1>

                <p className="text-muted-foreground mt-1">
                    Monitor, investigate, and resolve security alerts
                </p>
            </div>

            <AlertTable />
            
        </div>
    )
}