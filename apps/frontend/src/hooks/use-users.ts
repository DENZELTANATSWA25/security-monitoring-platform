"use client";

import {
    useSyncExternalStore,
} from "react";

import { useQuery } from "@tanstack/react-query";

import {
    getUsers,
    getCurrentUser,
} from "@/services/users.service";

import {
    subscribeToAuth,
    getAuthSnapshot,
    getServerAuthSnapshot,
} from "@/lib/auth";

export function useUsers() {
    return useQuery({
        queryKey: ["users"],
        queryFn: getUsers,
    });
}

export function useCurrentUser() {
    const token = useSyncExternalStore(
        subscribeToAuth,
        getAuthSnapshot,
        getServerAuthSnapshot
    );

    return useQuery({
        queryKey: ["current-user"],
        queryFn: getCurrentUser,
        enabled: Boolean(token),
        retry: false,
    });
}