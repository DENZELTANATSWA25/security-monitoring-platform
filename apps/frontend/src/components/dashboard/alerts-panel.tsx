"use client";

import { useState } from "react";

import {
    useAlerts,
    useResolveAlert,
} from "@/hooks/use-alerts";
import { useCurrentUser } from "@/hooks/use-users";
import { canResolveAlerts } from "@/lib/permissions";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function AlertsPanel() {
    const {
        data,
        isLoading,
        isError,
    } = useAlerts();

    const {
        data: currentUser,
    } = useCurrentUser();

    const resolveAlertMutation = useResolveAlert();

    const [mutationError, setMutationError] =
        useState<string | null>(null);

    if (isLoading) {
        return (
            <div className="mt-10">
                <p>Loading alerts...</p>
            </div>
        );
    }

    if (isError) {
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
        setMutationError(null);

        try {
            await resolveAlertMutation.mutateAsync(id);
        } catch {
            setMutationError(
                "Failed to resolve the alert. Please try again."
            );
        }
    }

    return (
        <div className="mt-10">
            <div className="mb-4 flex items-center justify-between">
                <h2 className="text-xl font-bold">
                    Active Security Alerts
                </h2>

                <Badge>
                    {activeAlerts.length}
                </Badge>
            </div>

            {mutationError && (
                <p className="mb-4 text-sm text-red-600">
                    {mutationError}
                </p>
            )}

            {activeAlerts.length === 0 ? (
                <div className="rounded-xl border p-6">
                    <p className="font-semibold">
                        No active alerts
                    </p>

                    <p className="mt-1 text-sm text-muted-foreground">
                        There are currently no unresolved security alerts.
                    </p>
                </div>
            ) : (
                <div className="space-y-4">
                    {activeAlerts.map((alert) => {
                        const isResolving =
                            resolveAlertMutation.isPending &&
                            resolveAlertMutation.variables === alert.id;

                        return (
                            <div
                                key={alert.id}
                                className="rounded-xl border p-5"
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

                                <div className="mt-4 flex items-center justify-between">
                                    <p className="text-sm text-muted-foreground">
                                        {new Date(
                                            alert.created_at
                                        ).toLocaleString()}
                                    </p>

                                    {canResolveAlerts(
                                        currentUser?.role
                                    ) && (
                                        <Button
                                            variant="outline"
                                            disabled={isResolving}
                                            onClick={() =>
                                                handleResolve(alert.id)
                                            }
                                        >
                                            {isResolving
                                                ? "Resolving..."
                                                : "Resolve"}
                                        </Button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}