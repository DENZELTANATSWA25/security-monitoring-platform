"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { useIncident } from "@/hooks/use-incidents";
import {
    useAssignableUsers,
    useCurrentUser,
} from "@/hooks/use-users";

import {
    assignIncident,
    updateIncidentStatus,
} from "@/services/incident.service";

import type { IncidentStatus } from "@/types/incident";

import { canManageIncidents } from "@/lib/permissions";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

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


export default function IncidentDetailsPage() {
    const params = useParams();

    const id = Number(params.id);

    const queryClient = useQueryClient();

    const {
        data: currentUser,
    } = useCurrentUser();

    const canManage =
        canManageIncidents(currentUser?.role);

    const {
        data: incident,
        isLoading,
        error,
    } = useIncident(id);

    const {
        data: assignableUsers = [],
        isLoading: isLoadingAssignableUsers,
    } = useAssignableUsers();

    const [
        selectedUserId,
        setSelectedUserId,
    ] = useState("");

    const [
        isAssigning,
        setIsAssigning,
    ] = useState(false);

    const [
        isUpdatingStatus,
        setIsUpdatingStatus,
    ] = useState(false);


    if (isLoading) {
        return (
            <div className="p-6">
                Loading incident...
            </div>
        );
    }


    if (error || !incident) {
        return (
            <div className="p-6 space-y-4">
                <p className="text-red-600">
                    Incident not found.
                </p>

                <Link
                    href="/incidents"
                    className="underline"
                >
                    Back to incidents
                </Link>
            </div>
        );
    }


    const currentIncident = incident;


    async function handleAssign() {
        if (!selectedUserId) {
            return;
        }

        const userId = Number(selectedUserId);

        if (Number.isNaN(userId)) {
            return;
        }

        try {
            setIsAssigning(true);

            await assignIncident(
                currentIncident.id,
                userId
            );

            setSelectedUserId("");

            await queryClient.invalidateQueries({
                queryKey: [
                    "incident",
                    currentIncident.id,
                ],
            });

            await queryClient.invalidateQueries({
                queryKey: ["incidents"],
            });
        } finally {
            setIsAssigning(false);
        }
    }


    async function handleStatusChange(
        status: IncidentStatus
    ) {
        try {
            setIsUpdatingStatus(true);

            await updateIncidentStatus(
                currentIncident.id,
                status
            );

            await queryClient.invalidateQueries({
                queryKey: [
                    "incident",
                    currentIncident.id,
                ],
            });

            await queryClient.invalidateQueries({
                queryKey: ["incidents"],
            });
        } finally {
            setIsUpdatingStatus(false);
        }
    }


    return (
        <div className="space-y-6">

            {/* Header */}

            <div>
                <Link
                    href="/incidents"
                    className="text-sm underline"
                >
                    ← Back to incidents
                </Link>

                <div className="flex items-center justify-between mt-4">

                    <div>
                        <h1 className="text-3xl font-bold">
                            {currentIncident.title}
                        </h1>

                        <p className="text-muted-foreground mt-1">
                            Incident #{currentIncident.id}
                        </p>
                    </div>

                    <Badge>
                        {currentIncident.status}
                    </Badge>

                </div>
            </div>


            {/* Incident Overview */}

            <Card>
                <CardHeader>
                    <CardTitle>
                        Incident Overview
                    </CardTitle>
                </CardHeader>

                <CardContent className="space-y-6">

                    <div>
                        <p className="text-sm text-muted-foreground">
                            Description
                        </p>

                        <p className="mt-1">
                            {currentIncident.description}
                        </p>
                    </div>


                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">

                        <div>
                            <p className="text-sm text-muted-foreground">
                                Severity
                            </p>

                            <p className="font-semibold mt-1">
                                {currentIncident.severity}
                            </p>
                        </div>


                        <div>
                            <p className="text-sm text-muted-foreground">
                                Status
                            </p>

                            <p className="font-semibold mt-1">
                                {currentIncident.status}
                            </p>
                        </div>


                        <div>
                            <p className="text-sm text-muted-foreground">
                                Assigned Analyst
                            </p>

                            <p className="font-semibold mt-1">
                                {
                                    currentIncident.assigned_to
                                    ?? "Unassigned"
                                }
                            </p>
                        </div>


                        <div>
                            <p className="text-sm text-muted-foreground">
                                Related Event
                            </p>

                            {currentIncident.event_id ? (
                                <Link
                                    href="/events"
                                    className="font-semibold underline"
                                >
                                    Event #{currentIncident.event_id}
                                </Link>
                            ) : (
                                <p className="font-semibold mt-1">
                                    None
                                </p>
                            )}
                        </div>

                    </div>

                </CardContent>
            </Card>


            {/* Analyst Assignment */}

            {canManage && (
                <Card>
                    <CardHeader>
                        <CardTitle>
                            Analyst Assignment
                        </CardTitle>
                    </CardHeader>

                    <CardContent>

                        <div className="flex flex-col sm:flex-row gap-3 max-w-xl">

                            <Select
                                value={selectedUserId}
                                onValueChange={(value) =>
                                    setSelectedUserId(value ?? "")
                                }
                                disabled={
                                    isAssigning
                                    || isLoadingAssignableUsers
                                }
                            >
                                <SelectTrigger className="w-full">
                                    <SelectValue
                                        placeholder={
                                            isLoadingAssignableUsers
                                                ? "Loading users..."
                                                : "Select analyst or administrator"
                                        }
                                    />
                                </SelectTrigger>

                                <SelectContent>
                                    {assignableUsers.map(
                                        (user) => (
                                            <SelectItem
                                                key={user.id}
                                                value={String(user.id)}
                                            >
                                                {user.full_name}
                                                {" — "}
                                                {user.role}
                                            </SelectItem>
                                        )
                                    )}
                                </SelectContent>
                            </Select>


                            <Button
                                onClick={handleAssign}
                                disabled={
                                    isAssigning
                                    || !selectedUserId
                                }
                            >
                                {
                                    isAssigning
                                        ? "Assigning..."
                                        : "Assign"
                                }
                            </Button>

                        </div>

                    </CardContent>
                </Card>
            )}


            {/* Status Management */}

            {canManage && (
                <Card>
                    <CardHeader>
                        <CardTitle>
                            Incident Status
                        </CardTitle>
                    </CardHeader>

                    <CardContent>

                        <div className="flex flex-wrap gap-3">

                            <Button
                                variant="outline"
                                disabled={isUpdatingStatus}
                                onClick={() =>
                                    handleStatusChange("OPEN")
                                }
                            >
                                Open
                            </Button>


                            <Button
                                variant="outline"
                                disabled={isUpdatingStatus}
                                onClick={() =>
                                    handleStatusChange(
                                        "IN_PROGRESS"
                                    )
                                }
                            >
                                In Progress
                            </Button>


                            <Button
                                variant="outline"
                                disabled={isUpdatingStatus}
                                onClick={() =>
                                    handleStatusChange("RESOLVED")
                                }
                            >
                                Resolve
                            </Button>


                            <Button
                                variant="outline"
                                disabled={isUpdatingStatus}
                                onClick={() =>
                                    handleStatusChange("CLOSED")
                                }
                            >
                                Close
                            </Button>

                        </div>

                    </CardContent>
                </Card>
            )}


            {/* Incident Timeline */}

            <Card>
                <CardHeader>
                    <CardTitle>
                        Incident Timeline
                    </CardTitle>
                </CardHeader>

                <CardContent className="space-y-4">

                    <div className="border-l-2 pl-4">
                        <p className="font-semibold">
                            Incident created
                        </p>

                        <p className="text-sm text-muted-foreground">
                            {new Date(
                                currentIncident.created_at
                            ).toLocaleString()}
                        </p>
                    </div>


                    <div className="border-l-2 pl-4">
                        <p className="font-semibold">
                            Last updated
                        </p>

                        <p className="text-sm text-muted-foreground">
                            {new Date(
                                currentIncident.updated_at
                            ).toLocaleString()}
                        </p>
                    </div>

                </CardContent>
            </Card>

        </div>
    );
}