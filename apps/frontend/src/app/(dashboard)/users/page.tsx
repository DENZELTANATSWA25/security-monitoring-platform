"use client";

import {
    useUsers,
    useCurrentUser,
    useUpdateUserRole,
    useUpdateUserStatus,
    useUpdateUserVerification,
} from "@/hooks/use-users";

import type { UserRole } from "@/types/user";

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


export default function UsersPage() {

    const {
        data,
        isLoading,
        error,
    } = useUsers();

    const {
        data: currentUser,
    } = useCurrentUser();

    const roleMutation =
        useUpdateUserRole();

    const statusMutation =
        useUpdateUserStatus();

    const verificationMutation =
        useUpdateUserVerification();


    if (isLoading) {
        return (
            <div className="p-6">
                Loading users...
            </div>
        );
    }


    if (error) {
        return (
            <div className="p-6 space-y-2">

                <p className="font-semibold text-red-600">
                    Failed to load users.
                </p>

                <p className="text-sm text-muted-foreground">
                    Make sure you are logged in with an administrator account.
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

                <p className="text-muted-foreground mt-1">
                    Manage SOC users and review account status.
                </p>

            </div>


            <Card>

                <CardHeader>

                    <div className="flex items-center justify-between">

                        <CardTitle>
                            User Directory
                        </CardTitle>

                        <Badge>
                            {data?.length ?? 0}
                        </Badge>

                    </div>

                </CardHeader>


                <CardContent>

                    <Table>

                        <TableHeader>

                            <TableRow>

                                <TableHead>
                                    User
                                </TableHead>

                                <TableHead>
                                    Email
                                </TableHead>

                                <TableHead>
                                    Role
                                </TableHead>

                                <TableHead>
                                    Status
                                </TableHead>

                                <TableHead>
                                    Verified
                                </TableHead>

                                <TableHead>
                                    Last Login
                                </TableHead>

                                <TableHead>
                                    Created
                                </TableHead>

                                <TableHead>
                                    Actions
                                </TableHead>

                            </TableRow>

                        </TableHeader>


                        <TableBody>

                            {data?.map((user) => (

                                <TableRow key={user.id}>

                                    {/* User */}

                                    <TableCell>

                                        <div>

                                            <p className="font-medium">
                                                {user.full_name}
                                            </p>

                                            <p className="text-sm text-muted-foreground">
                                                @{user.username}
                                            </p>

                                        </div>

                                    </TableCell>


                                    {/* Email */}

                                    <TableCell>
                                        {user.email}
                                    </TableCell>


                                    {/* Role */}

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


                                    {/* Status */}

                                    <TableCell>

                                        {user.is_active ? (

                                            <span className="font-medium text-green-600">
                                                Active
                                            </span>

                                        ) : (

                                            <span className="font-medium text-red-600">
                                                Inactive
                                            </span>

                                        )}

                                    </TableCell>


                                    {/* Verified */}

                                    <TableCell>

                                        {user.is_verified
                                            ? "Yes"
                                            : "No"}

                                    </TableCell>


                                    {/* Last login */}

                                    <TableCell>

                                        {user.last_login
                                            ? new Date(
                                                user.last_login
                                            ).toLocaleString()
                                            : "Never"}

                                    </TableCell>


                                    {/* Created */}

                                    <TableCell>

                                        {new Date(
                                            user.created_at
                                        ).toLocaleDateString()}

                                    </TableCell>


                                    {/* Actions */}

                                    <TableCell>

                                        {currentUser?.id === user.id ? (

                                            <span className="text-sm text-muted-foreground">
                                                Current user
                                            </span>

                                        ) : (

                                            <div className="flex flex-wrap items-center gap-2">

                                                <select
                                                    value={user.role}
                                                    disabled={roleMutation.isPending}
                                                    onChange={(event) =>
                                                        roleMutation.mutate({
                                                            userId: user.id,
                                                            role: event.target.value as UserRole,
                                                        })
                                                    }
                                                    className="
                                                        h-9
                                                        rounded-md
                                                        border
                                                        bg-background
                                                        px-3
                                                        text-sm
                                                    "
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
                                                    disabled={statusMutation.isPending}
                                                    onClick={() =>
                                                        statusMutation.mutate({
                                                            userId: user.id,
                                                            isActive: !user.is_active,
                                                        })
                                                    }
                                                >
                                                    {user.is_active
                                                        ? "Deactivate"
                                                        : "Activate"}
                                                </Button>


                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    disabled={verificationMutation.isPending}
                                                    onClick={() =>
                                                        verificationMutation.mutate({
                                                            userId: user.id,
                                                            isVerified: !user.is_verified,
                                                        })
                                                    }
                                                >
                                                    {user.is_verified
                                                        ? "Unverify"
                                                        : "Verify"}
                                                </Button>

                                            </div>

                                        )}

                                    </TableCell>

                                </TableRow>

                            ))}

                        </TableBody>

                    </Table>

                </CardContent>

            </Card>

        </div>
    );
}