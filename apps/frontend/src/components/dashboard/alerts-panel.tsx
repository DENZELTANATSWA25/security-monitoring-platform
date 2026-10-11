"use client";

import { useState } from "react";
import Link from "next/link";

import {
    AlertTriangle,
    ArrowUpRight,
    CheckCircle2,
    Clock3,
    RefreshCw,
    ShieldAlert,
} from "lucide-react";

import {
    useAlerts,
    useResolveAlert,
} from "@/hooks/use-alerts";

import { useCurrentUser } from "@/hooks/use-users";
import { canResolveAlerts } from "@/lib/permissions";

import {
    Card,
    CardContent,
    CardHeader,
} from "@/components/ui/card";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function AlertsPanel() {
    const {
        data,
        isLoading,
        isError,
        isFetching,
        refetch,
    } = useAlerts();

    const {
        data: currentUser,
    } = useCurrentUser();

    const resolveAlertMutation = useResolveAlert();

    const [mutationError, setMutationError] =
        useState<string | null>(null);

    const activeAlerts =
        data?.filter((alert) => !alert.resolved) ?? [];

    const canResolve = canResolveAlerts(currentUser?.role);

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

    function severityClass(severity: string) {
        switch (severity.toUpperCase()) {
            case "CRITICAL":
                return "border-red-500/30 bg-red-500/10 text-red-500";

            case "HIGH":
            case "ERROR":
                return "border-orange-500/30 bg-orange-500/10 text-orange-500";

            case "WARNING":
            case "MEDIUM":
                return "border-amber-500/30 bg-amber-500/10 text-amber-500";

            default:
                return "border-blue-500/30 bg-blue-500/10 text-blue-500";
        }
    }

    return (
        <Card className="overflow-hidden">
            <CardHeader className="border-b border-border/70">
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div className="flex items-start gap-3">
                        <div className="flex size-10 items-center justify-center rounded-xl bg-red-500/10 text-red-500">
                            <ShieldAlert className="size-5" />
                        </div>

                        <div>
                            <h2 className="text-base font-semibold">
                                Active Security Alerts
                            </h2>

                            <p className="mt-1 text-sm text-muted-foreground">
                                Unresolved threats requiring security review
                            </p>
                        </div>
                    </div>

                    <Badge
                        variant="outline"
                        className="rounded-full px-3 py-1"
                    >
                        {activeAlerts.length} active
                    </Badge>
                </div>

                <div className="flex flex-wrap items-center gap-2 pt-3">
                    <Button
                        variant="outline"
                        size="sm"
                        disabled={isFetching}
                        onClick={() => void refetch()}
                    >
                        <RefreshCw
                            className={`mr-2 size-4 ${
                                isFetching ? "animate-spin" : ""
                            }`}
                        />
                        Refresh
                    </Button>

                    <Link
                        href="/alerts"
                        className="inline-flex h-8 items-center justify-center gap-2 rounded-md border border-input bg-background px-3 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground"
                    >
                        View all alerts
                        <ArrowUpRight className="size-4" />
                    </Link>
                </div>
            </CardHeader>

            <CardContent className="p-4 sm:p-5">
                {mutationError && (
                    <div
                        role="alert"
                        className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive"
                    >
                        {mutationError}
                    </div>
                )}

                {isLoading ? (
                    <div
                        role="status"
                        className="flex min-h-32 items-center justify-center gap-3 text-sm text-muted-foreground"
                    >
                        <RefreshCw className="size-4 animate-spin" />
                        Loading security alerts...
                    </div>
                ) : isError ? (
                    <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center">
                        <AlertTriangle className="mx-auto mb-3 size-6 text-destructive" />

                        <h3 className="font-semibold">
                            Unable to load security alerts
                        </h3>

                        <p className="mt-2 text-sm text-muted-foreground">
                            The alerts service could not be reached.
                        </p>

                        <Button
                            variant="outline"
                            size="sm"
                            className="mt-4"
                            onClick={() => void refetch()}
                        >
                            Try again
                        </Button>
                    </div>
                ) : activeAlerts.length === 0 ? (
                    <div className="flex min-h-32 flex-col items-center justify-center rounded-xl border border-dashed border-border/70 px-4 py-6 text-center">
                        <div className="mb-3 flex size-11 items-center justify-center rounded-full bg-emerald-500/10">
                            <CheckCircle2 className="size-6 text-emerald-500" />
                        </div>

                        <h3 className="font-semibold">
                            No active alerts
                        </h3>

                        <p className="mt-1 max-w-md text-sm text-muted-foreground">
                            There are currently no unresolved security alerts.
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {activeAlerts.map((alert) => {
                            const isResolving =
                                resolveAlertMutation.isPending &&
                                resolveAlertMutation.variables === alert.id;

                            return (
                                <div
                                    key={alert.id}
                                    className="rounded-xl border border-border/70 bg-background/40 p-4 transition-colors hover:bg-accent/30"
                                >
                                    <div className="flex flex-wrap items-start justify-between gap-3">
                                        <div className="min-w-0 flex-1">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <AlertTriangle className="size-4 text-amber-500" />

                                                <h3 className="break-words text-sm font-semibold">
                                                    {alert.alert_type}
                                                </h3>
                                            </div>

                                            <p className="mt-2 break-words text-sm text-muted-foreground">
                                                {alert.message}
                                            </p>
                                        </div>

                                        <Badge
                                            variant="outline"
                                            className={severityClass(alert.severity)}
                                        >
                                            {alert.severity}
                                        </Badge>
                                    </div>

                                    <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-3">
                                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                            <Clock3 className="size-3.5" />

                                            <time dateTime={alert.created_at}>
                                                {new Date(
                                                    alert.created_at
                                                ).toLocaleString()}
                                            </time>
                                        </div>

                                        {canResolve && (
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                disabled={
                                                    resolveAlertMutation.isPending
                                                }
                                                onClick={() =>
                                                    void handleResolve(alert.id)
                                                }
                                            >
                                                {isResolving ? (
                                                    <>
                                                        <RefreshCw className="mr-2 size-4 animate-spin" />
                                                        Resolving...
                                                    </>
                                                ) : (
                                                    <>
                                                        <CheckCircle2 className="mr-2 size-4" />
                                                        Resolve
                                                    </>
                                                )}
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}