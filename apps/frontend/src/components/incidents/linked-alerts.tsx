"use client";

import { useMemo, useState } from "react";
import axios from "axios";

import { useAlerts } from "@/hooks/use-alerts";

import {
    useIncidentAlertLinks,
    useLinkAlertToIncident,
} from "@/hooks/use-incident-links";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";


interface LinkedAlertsProps {
    incidentId: number;
    canManage: boolean;
}


function formatDate(value: string) {
    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return date.toLocaleString();
}


function getErrorMessage(error: unknown) {
    if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
            return detail;
        }
    }

    return "Unable to link the alert.";
}


export default function LinkedAlerts({
    incidentId,
    canManage,
}: LinkedAlertsProps) {
    const [selectedAlertId, setSelectedAlertId] =
        useState("");

    const [mutationError, setMutationError] =
        useState<string | null>(null);

    const {
        data: links = [],
        isLoading,
        error,
    } = useIncidentAlertLinks(incidentId);

    const {
        data: alerts = [],
        isLoading: isLoadingAlerts,
    } = useAlerts();

    const linkAlertMutation =
        useLinkAlertToIncident(incidentId);


    /**
     * Alerts already attached to the incident should not be offered
     * again in the linkage control.
     *
     * The backend unique constraint remains the final integrity guard.
     */
    const availableAlerts = useMemo(() => {
        const linkedAlertIds = new Set(
            links.map((link) => link.alert_id)
        );

        return alerts.filter(
            (alert) =>
                !linkedAlertIds.has(alert.id)
        );
    }, [
        alerts,
        links,
    ]);


    async function handleLinkAlert() {
        if (!selectedAlertId) {
            return;
        }

        const alertId = Number(selectedAlertId);

        if (!Number.isInteger(alertId)) {
            return;
        }

        try {
            setMutationError(null);

            await linkAlertMutation.mutateAsync(
                alertId
            );

            setSelectedAlertId("");
        } catch (mutationFailure) {
            setMutationError(
                getErrorMessage(mutationFailure)
            );
        }
    }


    return (
        <Card>
            <CardHeader>
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                        <CardTitle>
                            Linked Alerts
                        </CardTitle>

                        <p className="mt-1 text-sm text-muted-foreground">
                            Alerts associated with this incident during
                            investigation.
                        </p>
                    </div>

                    <Badge variant="outline">
                        {links.length} linked
                    </Badge>
                </div>
            </CardHeader>

            <CardContent className="space-y-6">
                {canManage && (
                    <div className="space-y-2">
                        <div className="flex flex-col gap-3 sm:flex-row">
                            <Select
                                value={selectedAlertId}
                                onValueChange={(value) => {
                                    setSelectedAlertId(
                                        value ?? ""
                                    );

                                    setMutationError(null);
                                }}
                                disabled={
                                    isLoadingAlerts
                                    || linkAlertMutation.isPending
                                    || availableAlerts.length === 0
                                }
                            >
                                <SelectTrigger className="w-full">
                                    <SelectValue
                                        placeholder={
                                            isLoadingAlerts
                                                ? "Loading alerts..."
                                                : availableAlerts.length === 0
                                                    ? "No additional alerts available"
                                                    : "Select an alert to link"
                                        }
                                    />
                                </SelectTrigger>

                                <SelectContent>
                                    {availableAlerts.map(
                                        (alert) => (
                                            <SelectItem
                                                key={alert.id}
                                                value={String(alert.id)}
                                            >
                                                #{alert.id}
                                                {" — "}
                                                {alert.alert_type}
                                                {" — "}
                                                {alert.severity}
                                            </SelectItem>
                                        )
                                    )}
                                </SelectContent>
                            </Select>

                            <Button
                                onClick={handleLinkAlert}
                                disabled={
                                    !selectedAlertId
                                    || linkAlertMutation.isPending
                                }
                            >
                                {linkAlertMutation.isPending
                                    ? "Linking..."
                                    : "Link Alert"}
                            </Button>
                        </div>

                        {mutationError && (
                            <p className="text-sm text-red-600">
                                {mutationError}
                            </p>
                        )}
                    </div>
                )}

                {isLoading ? (
                    <p className="text-sm text-muted-foreground">
                        Loading linked alerts...
                    </p>
                ) : error ? (
                    <p className="text-sm text-red-600">
                        Unable to load linked alerts.
                    </p>
                ) : links.length === 0 ? (
                    <div className="rounded-md border border-dashed p-6 text-center">
                        <p className="font-medium">
                            No alerts linked
                        </p>

                        <p className="mt-1 text-sm text-muted-foreground">
                            Alerts associated with this investigation
                            will appear here.
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {links.map((link) => (
                            <div
                                key={link.id}
                                className="rounded-md border p-4"
                            >
                                <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
                                    <div className="min-w-0">
                                        <div className="flex flex-wrap items-center gap-2">
                                            <p className="font-semibold">
                                                Alert #{link.alert.id}
                                                {" — "}
                                                {link.alert.alert_type}
                                            </p>

                                            <Badge variant="outline">
                                                {link.alert.severity}
                                            </Badge>

                                            <Badge
                                                variant={
                                                    link.alert.resolved
                                                        ? "secondary"
                                                        : "outline"
                                                }
                                            >
                                                {link.alert.resolved
                                                    ? "Resolved"
                                                    : "Active"}
                                            </Badge>
                                        </div>

                                        <p className="mt-2 text-sm">
                                            {link.alert.message}
                                        </p>
                                    </div>

                                    <p className="shrink-0 text-sm text-muted-foreground">
                                        {formatDate(
                                            link.alert.created_at
                                        )}
                                    </p>
                                </div>

                                <div className="mt-4 grid gap-4 border-t pt-4 sm:grid-cols-2">
                                    <div>
                                        <p className="text-xs text-muted-foreground">
                                            Linked by
                                        </p>

                                        <p className="mt-1 text-sm font-medium">
                                            {link.linked_by?.full_name
                                                ?? "Unknown user"}
                                        </p>
                                    </div>

                                    <div>
                                        <p className="text-xs text-muted-foreground">
                                            Linked
                                        </p>

                                        <p className="mt-1 text-sm font-medium">
                                            {formatDate(
                                                link.created_at
                                            )}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}