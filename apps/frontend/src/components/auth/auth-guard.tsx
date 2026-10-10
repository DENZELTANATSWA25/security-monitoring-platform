"use client";

import {
    useEffect,
    useSyncExternalStore,
} from "react";

import { useRouter } from "next/navigation";

import { DEV_AUTH_BYPASS } from "@/lib/auth-config";

import {
    getAuthSnapshot,
    getServerAuthSnapshot,
    subscribeToAuth,
} from "@/lib/auth";

import { useCurrentUser } from "@/hooks/use-users";

export default function AuthGuard({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();

    const isHydrated = useSyncExternalStore(
        () => () => {},
        () => true,
        () => false
    );

    const isAuthenticated = useSyncExternalStore(
        subscribeToAuth,
        getAuthSnapshot,
        getServerAuthSnapshot
    );

    const {
        data: currentUser,
        isPending,
        isError,
    } = useCurrentUser();

    useEffect(() => {
        if (DEV_AUTH_BYPASS || !isHydrated) {
            return;
        }

        if (!isAuthenticated) {
            router.replace("/login");
            return;
        }

        if (isPending) {
            return;
        }

        if (isError) {
            router.replace("/login");
        }
    }, [
        isHydrated,
        isAuthenticated,
        isPending,
        isError,
        router,
    ]);

    if (DEV_AUTH_BYPASS) {
        return children;
    }

    if (
        !isHydrated ||
        !isAuthenticated ||
        isPending
    ) {
        return (
            <div className="flex min-h-screen items-center justify-center">
                Checking authentication...
            </div>
        );
    }

    if (isError || !currentUser) {
        return null;
    }

    return children;
}