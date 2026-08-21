"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useAlerts } from "@/hooks/use-alerts";
import { resolveAlert } from "@/services/alerts.service";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function AlertsPanel() {
    const {
        data,
        isLoading,
        error,
    } = useAlerts();

    const queryClient = useQueryClient();

    const [resolvingId, setResolvingId] = useState<number | null>(null);

    if (isLoading) {
        return (
            <div className="mt-10">
                <p>Loading alerts...</p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="mt-10">
                <p className="text-red-600">
                    Failed to load alerts.
                </p>
            </div>
        );
    }

    const activeAlerts =
        data?.filter((alert) => !alert.resolved) ?? [];

    async function handleResolve(id: number) {
        try {
            setResolvingId(id);

            await resolveAlert(id);

            await queryClient.invalidateQueries({
                queryKey: ["alerts"],
            });

            await queryClient.invalidateQueries({
                queryKey: ["dashboard-summary"],
            });

        } finally {
            setResolvingId(null);
        }
    }

    return (
        <div className="mt-10">

            <div className="flex items-center justify-between mb-4">

                <h2 className="text-xl font-bold">
                    Active Security Alerts
                </h2>

                <Badge>
                    {activeAlerts.length}
                </Badge>

            </div>

            {activeAlerts.length === 0 ? (

                <div className="border rounded-xl p-6">

                    <p className="font-semibold">
                        No active alerts
                    </p>

                    <p className="text-sm text-muted-foreground mt-1">
                        There are currently no unresolved security alerts.
                    </p>

                </div>

            ) : (

                <div className="space-y-4">

                    {activeAlerts.map((alert) => (

                        <div
                            key={alert.id}
                            className="border rounded-xl p-5"
                        >

                            <div className="flex items-start justify-between gap-4">

                                <div>

                                    <h3 className="font-bold">
                                        {alert.alert_type}
                                    </h3>

                                    <p className="mt-2">
                                        {alert.message}
                                    </p>

                                </div>

                                <Badge>
                                    {alert.severity}
                                </Badge>

                            </div>

                            <div className="flex items-center justify-between mt-4">

                                <p className="text-sm text-muted-foreground">
                                    {new Date(
                                        alert.created_at
                                    ).toLocaleString()}
                                </p>

                                <Button
                                    variant="outline"
                                    disabled={resolvingId === alert.id}
                                    onClick={() =>
                                        handleResolve(alert.id)
                                    }
                                >
                                    {resolvingId === alert.id
                                        ? "Resolving..."
                                        : "Resolve"}
                                </Button>

                            </div>

                        </div>

                    ))}

                </div>

            )}

        </div>
    );
}