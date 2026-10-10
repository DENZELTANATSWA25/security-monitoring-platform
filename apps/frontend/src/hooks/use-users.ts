"use client";

import {
    useSyncExternalStore,
} from "react";

import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import {
    getUsers,
    getCurrentUser,
    getAssignableUsers,
    updateUserRole,
    updateUserStatus,
    updateUserVerification,
} from "@/services/users.service";

import { UserRole } from "@/types/user";

import {
    subscribeToAuth,
    getAuthSnapshot,
    getServerAuthSnapshot,
} from "@/lib/auth";

export function useUsers(enabled = true) {
    return useQuery({
        queryKey: ["users"],
        queryFn: getUsers,
        enabled,
        retry: false,
    });
}

export function useAssignableUsers() {
    return useQuery({
        queryKey: ["assignable-users"],
        queryFn: getAssignableUsers,
    });
}

export function useCurrentUser() {
    const isAuthenticated = useSyncExternalStore(
        subscribeToAuth,
        getAuthSnapshot,
        getServerAuthSnapshot
    );

    return useQuery({
        queryKey: ["current-user", isAuthenticated],
        queryFn: getCurrentUser,
        enabled: isAuthenticated,
        retry: false,
        staleTime: 0,
        refetchOnMount: "always",
    });
}

export function useUpdateUserRole() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            userId,
            role,
        }: {
            userId: number;
            role: UserRole;
        }) =>
            updateUserRole(
                userId,
                role
            ),

        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["users"]
            });
        },
    });
}

export function useUpdateUserStatus() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            userId,
            isActive,
        }: {
            userId: number;
            isActive: boolean;
        }) =>
            updateUserStatus(
                userId,
                isActive
            ),

        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["users"]
            });
        },
    });
}

export function useUpdateUserVerification() {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: ({
            userId,
            isVerified,
        }: {
            userId: number;
            isVerified: boolean;
        }) =>
            updateUserVerification(
                userId,
                isVerified
            ),

        onSuccess: async () => {
            await queryClient.invalidateQueries({
                queryKey: ["users"]
            });
        },
    });
}

