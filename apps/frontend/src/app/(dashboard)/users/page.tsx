"use client";

import { useUsers } from "@/hooks/use-users";

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

                            </TableRow>

                        </TableHeader>


                        <TableBody>

                            {data?.map((user) => (

                                <TableRow key={user.id}>

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


                                    <TableCell>

                                        {user.is_verified
                                            ? "Yes"
                                            : "No"}

                                    </TableCell>


                                    <TableCell>

                                        {user.last_login
                                            ? new Date(
                                                user.last_login
                                            ).toLocaleString()
                                            : "Never"}

                                    </TableCell>


                                    <TableCell>

                                        {new Date(
                                            user.created_at
                                        ).toLocaleDateString()}

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