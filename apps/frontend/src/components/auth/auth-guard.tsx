"use client";

import { useEffect, useSyncExternalStore } from "react";
import { useRouter } from "next/navigation";

import { DEV_AUTH_BYPASS } from "@/lib/auth-config";
import { useCurrentUser } from "@/hooks/use-users";

import {
  getAuthSnapshot,
  getServerAuthSnapshot,
  subscribeToAuth,
} from "@/lib/auth";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const isAuthenticated = useSyncExternalStore(
    subscribeToAuth,
    getAuthSnapshot,
    getServerAuthSnapshot,
  );

  const { data: currentUser, isLoading, isError } = useCurrentUser();

  useEffect(() => {
    if (DEV_AUTH_BYPASS) {
      return;
    }

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (!isLoading && (isError || !currentUser)) {
      router.replace("/login");
    }
  }, [isAuthenticated, isLoading, isError, currentUser, router]);

  if (DEV_AUTH_BYPASS) {
    return children;
  }

  if (!isAuthenticated || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Checking authentication
      </div>
    );
  }

  if (isError || !currentUser) {
    return null;
  }

  return children;
}
