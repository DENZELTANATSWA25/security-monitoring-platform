"use client";

import { useState } from "react";
import axios from "axios";

import {
    useUsers,
    useCurrentUser,
    useUpdateUserRole,
    useUpdateUserStatus,
    useUpdateUserVerification,
} from "@/hooks/use-users";

import { canViewUsers } from "@/lib/permissions";

import type {
    User,
    UserRole,
} from "@/types/user";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";


type PendingAction = {
    userId: number;
    action: "role" | "status" | "verification";
} | null;


function getErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        if (typeof detail === "string") {
            return detail;
        }

        return error.message;
    }

    if (error instanceof Error) {
        return error.message;
    }

    return "An unexpected error occurred.";
}


function formatDate(value: string | null): string {
    if (!value) {
        return "Never";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Unknown";
    }

    return date.toLocaleString();
}


export default function UsersPage() {
    const {
        data: currentUser,
        isLoading: isLoadingCurrentUser,
        isPending: isPendingCurrentUser,
        error: currentUserError,
    } = useCurrentUser();

    const isAdmin = canViewUsers(currentUser?.role);

    const {
        data: users = [],
        isLoading: isLoadingUsers,
        error: usersError,
        refetch: refetchUsers,
    } = useUsers(isAdmin);

    const roleMutation = useUpdateUserRole();
    const statusMutation = useUpdateUserStatus();
    const verificationMutation = useUpdateUserVerification();

    const [pendingAction, setPendingAction] =
        useState<PendingAction>(null);

    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);


    function clearMessages() {
        setError(null);
        setSuccess(null);
    }


    function isUserBusy(userId: number): boolean {
        return pendingAction?.userId === userId;
    }


    async function changeRole(
        user: User,
        role: UserRole
    ) {
        if (role === user.role) {
            return;
        }

        if (
            !window.confirm(
                `Change ${user.username}'s role from ${user.role} to ${role}?`
            )
        ) {
            return;
        }

        clearMessages();

        setPendingAction({
            userId: user.id,
            action: "role",
        });

        try {
            await roleMutation.mutateAsync({
                userId: user.id,
                role,
            });

            setSuccess(
                `${user.username}'s role was updated to ${role}.`
            );
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setPendingAction(null);
        }
    }


    async function changeStatus(user: User) {
        const nextStatus = !user.is_active;

        const action = nextStatus
            ? "activate"
            : "deactivate";

        if (
            !window.confirm(
                `Are you sure you want to ${action} ${user.username}'s account?`
            )
        ) {
            return;
        }

        clearMessages();

        setPendingAction({
            userId: user.id,
            action: "status",
        });

        try {
            await statusMutation.mutateAsync({
                userId: user.id,
                isActive: nextStatus,
            });

            setSuccess(
                `${user.username}'s account was ${
                    nextStatus ? "activated" : "deactivated"
                }.`
            );
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setPendingAction(null);
        }
    }


    async function changeVerification(user: User) {
        const nextVerification = !user.is_verified;

        const action = nextVerification
            ? "verify"
            : "unverify";

        if (
            !window.confirm(
                `Are you sure you want to ${action} ${user.username}?`
            )
        ) {
            return;
        }

        clearMessages();

        setPendingAction({
            userId: user.id,
            action: "verification",
        });

        try {
            await verificationMutation.mutateAsync({
                userId: user.id,
                isVerified: nextVerification,
            });

            setSuccess(
                `${user.username} was ${
                    nextVerification ? "verified" : "unverified"
                }.`
            );
        } catch (err) {
            setError(getErrorMessage(err));
        } finally {
            setPendingAction(null);
        }
    }


    if (isLoadingCurrentUser || isPendingCurrentUser) {
        return (
            <div className="p-6">
                Loading account permissions...
            </div>
        );
    }


    if (currentUserError) {
        return (
            <div className="p-6 space-y-2">
                <h1 className="text-2xl font-bold">
                    Unable to verify permissions
                </h1>

                <p className="text-muted-foreground">
                    {getErrorMessage(currentUserError)}
                </p>
            </div>
        );
    }


    if (!isAdmin) {
        return (
            <div className="p-6 space-y-2">
                <h1 className="text-2xl font-bold">
                    Access Denied
                </h1>

                <p className="text-muted-foreground">
                    Only administrators can manage users.
                </p>
            </div>
        );
    }


    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold">
                    Users
                </h1>

                <p className="mt-1 text-muted-foreground">
                    Manage SOC user roles, account access,
                    and verification.
                </p>
            </div>


            {error && (
                <div
                    role="alert"
                    className="rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-700"
                >
                    {error}
                </div>
            )}


            {success && (
                <div
                    role="status"
                    className="rounded-md border border-green-300 bg-green-50 p-4 text-sm text-green-700"
                >
                    {success}
                </div>
            )}


            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between gap-4">
                        <CardTitle>
                            User Directory
                        </CardTitle>

                        <div className="flex items-center gap-3">
                            <Badge variant="secondary">
                                {users.length} users
                            </Badge>

                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                    clearMessages();
                                    void refetchUsers();
                                }}
                                disabled={isLoadingUsers}
                            >
                                Refresh
                            </Button>
                        </div>
                    </div>
                </CardHeader>


                <CardContent>
                    {isLoadingUsers ? (
                        <p className="py-8 text-center text-muted-foreground">
                            Loading users...
                        </p>
                    ) : usersError ? (
                        <div className="space-y-3 py-6">
                            <p className="font-medium text-red-600">
                                Failed to load users.
                            </p>

                            <p className="text-sm text-muted-foreground">
                                {getErrorMessage(usersError)}
                            </p>

                            <Button
                                variant="outline"
                                onClick={() => void refetchUsers()}
                            >
                                Try Again
                            </Button>
                        </div>
                    ) : users.length === 0 ? (
                        <p className="py-8 text-center text-muted-foreground">
                            No users found.
                        </p>
                    ) : (
                        <div className="overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>User</TableHead>
                                        <TableHead>Email</TableHead>
                                        <TableHead>Role</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Verified</TableHead>
                                        <TableHead>Last Login</TableHead>
                                        <TableHead>Created</TableHead>
                                        <TableHead>Actions</TableHead>
                                    </TableRow>
                                </TableHeader>

                                <TableBody>
                                    {users.map((user) => {
                                        const isCurrentUser =
                                            currentUser?.id === user.id;

                                        const isBusy =
                                            isUserBusy(user.id);

                                        const isAnyMutationPending =
                                            pendingAction !== null;

                                        return (
                                            <TableRow key={user.id}>
                                                <TableCell>
                                                    <p className="font-medium">
                                                        {user.full_name}
                                                    </p>

                                                    <p className="text-sm text-muted-foreground">
                                                        @{user.username}
                                                    </p>
                                                </TableCell>

                                                <TableCell>
                                                    {user.email}
                                                </TableCell>

                                                <TableCell>
                                                    <Badge
                                                        variant={
                                                            user.role === "admin"
                                                                ? "destructive"
                                                                : user.role === "analyst"
                                                                ? "default"
                                                                : "secondary"
                                                        }
                                                    >
                                                        {user.role.toUpperCase()}
                                                    </Badge>
                                                </TableCell>

                                                <TableCell>
                                                    <span
                                                        className={
                                                            user.is_active
                                                                ? "font-medium text-green-600"
                                                                : "font-medium text-red-600"
                                                        }
                                                    >
                                                        {user.is_active
                                                            ? "Active"
                                                            : "Inactive"}
                                                    </span>
                                                </TableCell>

                                                <TableCell>
                                                    {user.is_verified
                                                        ? "Yes"
                                                        : "No"}
                                                </TableCell>

                                                <TableCell>
                                                    {formatDate(user.last_login)}
                                                </TableCell>

                                                <TableCell>
                                                    {new Date(
                                                        user.created_at
                                                    ).toLocaleDateString()}
                                                </TableCell>

                                                <TableCell>
                                                    {isCurrentUser ? (
                                                        <span className="text-sm text-muted-foreground">
                                                            Current user
                                                        </span>
                                                    ) : (
                                                        <div className="flex flex-wrap items-center gap-2">
                                                            <select
                                                                aria-label={`Role for ${user.username}`}
                                                                value={user.role}
                                                                disabled={isAnyMutationPending}
                                                                onChange={(event) =>
                                                                    void changeRole(
                                                                        user,
                                                                        event.target.value as UserRole
                                                                    )
                                                                }
                                                                className="h-9 rounded-md border bg-background px-3 text-sm"
                                                            >
                                                                <option value="viewer">
                                                                    Viewer
                                                                </option>

                                                                <option value="analyst">
                                                                    Analyst
                                                                </option>

                                                                <option value="admin">
                                                                    Admin
                                                                </option>
                                                            </select>

                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                disabled={isAnyMutationPending}
                                                                onClick={() =>
                                                                    void changeStatus(user)
                                                                }
                                                            >
                                                                {isBusy &&
                                                                pendingAction?.action === "status"
                                                                    ? "Updating..."
                                                                    : user.is_active
                                                                    ? "Deactivate"
                                                                    : "Activate"}
                                                            </Button>

                                                            <Button
                                                                variant="outline"
                                                                size="sm"
                                                                disabled={isAnyMutationPending}
                                                                onClick={() =>
                                                                    void changeVerification(user)
                                                                }
                                                            >
                                                                {isBusy &&
                                                                pendingAction?.action === "verification"
                                                                    ? "Updating..."
                                                                    : user.is_verified
                                                                    ? "Unverify"
                                                                    : "Verify"}
                                                            </Button>
                                                        </div>
                                                    )}
                                                </TableCell>
                                            </TableRow>
                                        );
                                    })}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}