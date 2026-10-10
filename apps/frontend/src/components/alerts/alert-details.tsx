"use client";

import { useAlertDetails } from "@/hooks/use-alerts";

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

import SeverityBadge from "./severity-badge";

interface AlertDetailsProps {
    alertId: number | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export default function AlertDetails({
    alertId,
    open,
    onOpenChange,
}: AlertDetailsProps) {
    const {
        data: alert,
        isLoading,
        isError,
        refetch,
    } = useAlertDetails(open ? alertId : null);

    return (
        <Dialog
            open={open}
            onOpenChange={onOpenChange}
        >
            <DialogContent className="max-w-xl">
                <DialogHeader>
                    <DialogTitle>
                        Alert Investigation
                    </DialogTitle>
                </DialogHeader>

                {isLoading ? (
                    <p>Loading alert details...</p>
                ) : isError ? (
                    <div className="space-y-3">
                        <p className="text-red-600">
                            Failed to load alert details.
                        </p>

                        <button
                            type="button"
                            onClick={() => refetch()}
                            className="text-sm underline"
                        >
                            Retry
                        </button>
                    </div>
                ) : alert ? (
                    <div className="space-y-4 text-sm">
                        <div>
                            <span className="font-semibold">
                                Alert ID:
                            </span>{" "}
                            {alert.id}
                        </div>

                        <div>
                            <span className="font-semibold">
                                Type:
                            </span>{" "}
                            {alert.alert_type}
                        </div>

                        <div>
                            <span className="font-semibold">
                                Severity:
                            </span>

                            <div className="mt-1">
                                <SeverityBadge
                                    severity={alert.severity}
                                />
                            </div>
                        </div>

                        <div>
                            <span className="font-semibold">
                                Status:
                            </span>{" "}
                            {alert.resolved
                                ? "Resolved"
                                : "Open"}
                        </div>

                        <div>
                            <span className="font-semibold">
                                Created:
                            </span>{" "}
                            {new Date(
                                alert.created_at
                            ).toLocaleString()}
                        </div>

                        <div>
                            <p className="font-semibold">
                                Description
                            </p>

                            <p className="mt-1 whitespace-pre-wrap text-muted-foreground">
                                {alert.message}
                            </p>
                        </div>
                    </div>
                ) : (
                    <p>Alert not found.</p>
                )}
            </DialogContent>
        </Dialog>
    );
}