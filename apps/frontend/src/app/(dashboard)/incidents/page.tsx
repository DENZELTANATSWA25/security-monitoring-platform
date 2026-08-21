"use client";

import Link from "next/link";

import { useIncidents } from "@/hooks/use-incidents";

import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";


export default function IncidentsPage() {

    const {
        data,
        isLoading,
        error,
    } = useIncidents();


    if (isLoading) {
        return (
            <div className="p-6">
                Loading incidents...
            </div>
        );
    }


    if (error) {
        return (
            <div className="p-6 text-red-600">
                Failed to load incidents.
            </div>
        );
    }


    return (

        <div className="space-y-6">

            <div>

                <h1 className="text-3xl font-bold">
                    Incidents
                </h1>

                <p className="text-muted-foreground mt-1">
                    Manage and investigate security incidents.
                </p>

            </div>


            <div className="grid gap-4">

                {data?.map((incident) => (

                    <Link
                        key={incident.id}
                        href={`/incidents/${incident.id}`}
                    >

                        <Card className="hover:bg-slate-50 transition">

                            <CardHeader>

                                <div className="flex justify-between">

                                    <CardTitle>
                                        {incident.title}
                                    </CardTitle>

                                    <Badge>
                                        {incident.status}
                                    </Badge>

                                </div>

                            </CardHeader>


                            <CardContent>

                                <div className="grid grid-cols-4 gap-4">

                                    <div>

                                        <p className="text-sm text-muted-foreground">
                                            Severity
                                        </p>

                                        <p className="font-semibold">
                                            {incident.severity}
                                        </p>

                                    </div>


                                    <div>

                                        <p className="text-sm text-muted-foreground">
                                            Assigned To
                                        </p>

                                        <p className="font-semibold">
                                            {incident.assigned_to ?? "Unassigned"}
                                        </p>

                                    </div>


                                    <div>

                                        <p className="text-sm text-muted-foreground">
                                            Event
                                        </p>

                                        <p className="font-semibold">
                                            {incident.event_id
                                                ? `Event #${incident.event_id}`
                                                : "None"}
                                        </p>

                                    </div>


                                    <div>

                                        <p className="text-sm text-muted-foreground">
                                            Created
                                        </p>

                                        <p className="font-semibold">
                                            {new Date(
                                                incident.created_at
                                            ).toLocaleString()}
                                        </p>

                                    </div>

                                </div>

                            </CardContent>

                        </Card>

                    </Link>

                ))}


                {data?.length === 0 && (

                    <Card>

                        <CardContent className="p-8 text-center">

                            No incidents found.

                        </CardContent>

                    </Card>

                )}

            </div>

        </div>
    );
}