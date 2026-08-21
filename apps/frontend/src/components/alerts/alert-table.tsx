"use client";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";

import { Button } from "@/components/ui/button";

import SeverityBadge from "./severity-badge";

import {
    useAlerts,
    useResolveAlert,
} from "@/hooks/use-alerts";


export default function AlertTable() {

    const {
        data,
        isLoading,
        error,
    } = useAlerts();

    const resolve = useResolveAlert();


    if (isLoading) {
        return (
            <div className="bg-white rounded-xl border p-6">
                Loading alerts...
            </div>
        );
    }


    if (error) {
        return (
            <div className="bg-white rounded-xl border p-6">

                <p className="font-semibold text-red-600">
                    Failed to load alerts.
                </p>

                <p className="text-sm text-muted-foreground mt-1">
                    Please check that the backend is running.
                </p>

            </div>
        );
    }


    if (!data || data.length === 0) {
        return (
            <div className="bg-white rounded-xl border p-6">

                <p className="font-semibold">
                    No security alerts
                </p>

                <p className="text-sm text-muted-foreground mt-1">
                    There are currently no alerts in the system.
                </p>

            </div>
        );
    }


    return (

        <div className="bg-white rounded-xl border p-5">

            <div className="flex items-center justify-between mb-5">

                <div>

                    <h2 className="text-xl font-bold">
                        Security Alerts
                    </h2>

                    <p className="text-sm text-muted-foreground mt-1">
                        {data.length} alert{data.length === 1 ? "" : "s"} total
                    </p>

                </div>

            </div>


            <Table>

                <TableHeader>

                    <TableRow>

                        <TableHead>
                            Severity
                        </TableHead>

                        <TableHead>
                            Type
                        </TableHead>

                        <TableHead>
                            Message
                        </TableHead>

                        <TableHead>
                            Status
                        </TableHead>

                        <TableHead>
                            Created
                        </TableHead>

                        <TableHead>
                            Action
                        </TableHead>

                    </TableRow>

                </TableHeader>


                <TableBody>

                    {data.map((alert) => (

                        <TableRow key={alert.id}>

                            <TableCell>

                                <SeverityBadge
                                    severity={alert.severity}
                                />

                            </TableCell>


                            <TableCell className="font-medium">

                                {alert.alert_type}

                            </TableCell>


                            <TableCell>

                                {alert.message ?? "No message"}

                            </TableCell>


                            <TableCell>

                                {alert.resolved ? (
                                    <span className="text-green-600 font-medium">
                                        Resolved
                                    </span>
                                ) : (
                                    <span className="text-red-600 font-medium">
                                        Open
                                    </span>
                                )}

                            </TableCell>


                            <TableCell className="text-sm text-muted-foreground">

                                {new Date(
                                    alert.created_at
                                ).toLocaleString()}

                            </TableCell>


                            <TableCell>

                                {!alert.resolved && (

                                    <Button
                                        size="sm"
                                        onClick={() =>
                                            resolve.mutate(alert.id)
                                        }
                                        disabled={resolve.isPending}
                                    >

                                        {resolve.isPending
                                            ? "Resolving..."
                                            : "Resolve"}

                                    </Button>

                                )}

                                {alert.resolved && (

                                    <span className="text-sm text-muted-foreground">
                                        No action
                                    </span>

                                )}

                            </TableCell>

                        </TableRow>

                    ))}

                </TableBody>

            </Table>

        </div>

    );
}