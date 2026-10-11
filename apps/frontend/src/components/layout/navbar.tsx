"use client";

import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";

import { useCurrentUser } from "@/hooks/use-users";
import { logout } from "@/services/auth.service";

import { Button } from "@/components/ui/button";
import ThemeSelector from "@/components/theme/theme-selector";

export default function Navbar() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const {
    data: currentUser,
    isLoading,
  } = useCurrentUser();

  function handleLogout() {
    logout();
    queryClient.clear();
    router.replace("/login");
  }

  function handleLogin() {
    router.push("/login");
  }

  return (
    <header
      className="
        flex h-[72px] min-w-0 items-center
        justify-between gap-2 px-2
        sm:gap-3 sm:px-5
        text-card-foreground
      "
    >
      {/* Application identity */}
      <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-3">
        <div
          className="
            hidden size-9 shrink-0 items-center justify-center
            rounded-lg border border-border bg-secondary
            sm:flex
          "
        >
          <ShieldCheck
            className="size-5 text-primary"
            aria-hidden="true"
          />
        </div>

        <div className="min-w-0">
          <h2
            className="
              truncate text-xs font-semibold
              sm:text-sm
            "
            title="Security Operations Center"
          >
            <span className="sm:hidden">Security SOC</span>
            <span className="hidden sm:inline">
              Security Operations Center
            </span>
          </h2>

          <p
            className="
              hidden truncate text-xs text-muted-foreground
              md:block
            "
          >
            Threat Monitoring Platform
          </p>
        </div>
      </div>

      {/* Header controls */}
      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <ThemeSelector />

        <div
          className="
            hidden items-center gap-2
            text-xs text-status-success
            lg:flex
          "
        >
          <span
            className="
              size-2 rounded-full
              bg-status-success
            "
            aria-hidden="true"
          />

          <span>System Online</span>
        </div>

        {isLoading ? (
          <span className="hidden text-sm text-muted-foreground sm:inline">
            Loading user...
          </span>
        ) : currentUser ? (
          <>
            <div className="hidden text-right lg:block">
              <p className="text-sm font-medium">
                {currentUser.full_name}
              </p>

              <p
                className="
                  text-xs uppercase tracking-wide
                  text-muted-foreground
                "
              >
                {currentUser.role}
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="shrink-0"
            >
              Logout
            </Button>
          </>
        ) : (
          <>
            <div className="hidden text-right lg:block">
              <p className="text-sm font-medium">
                Guest
              </p>

              <p className="text-xs text-muted-foreground">
                Dev Mode
              </p>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handleLogin}
              className="shrink-0"
            >
              Login
            </Button>
          </>
        )}
      </div>
    </header>
  );
}