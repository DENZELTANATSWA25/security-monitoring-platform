"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { DEV_AUTH_BYPASS } from "@/lib/auth-config";
import { useCurrentUser } from "@/hooks/use-users";
import { getAccessToken } from "@/lib/auth";

export default function AuthGuard({
    children,
}: {
    children: React.ReactNode;
}) {
    const router = useRouter();

    const token = getAccessToken();

    const {
        data: currentUser,
        isLoading,
    } = useCurrentUser();

    useEffect(() => {
        if (DEV_AUTH_BYPASS) {
            return;
        }

        if (!token) {
            router.replace("/login");
            return;
        }

        if (!isLoading && !currentUser) {
            router.replace("/login");
        }
    }, [
        token,
        isLoading,
        currentUser,
        router,
    ]);

    if (DEV_AUTH_BYPASS) {
        return children;
    }

    if (!token || isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                Checking authentication
            </div>
        );
    }

    if (!currentUser) {
        return null;
    }

    return children;
}    
