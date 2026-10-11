"use client";

import DetectionRulesManager from "@/components/detection-rules/detection-rules-manager";

import { useCurrentUser } from "@/hooks/use-users";
import { canManageRules } from "@/lib/permissions";

export default function DetectionRulesPage() {
  const {
    data: currentUser,
    isLoading,
    isPending,
    error,
  } = useCurrentUser();

  // Wait until the current user's permissions are available.
  if (isLoading || isPending) {
    return (
      <div className="p-6 text-muted-foreground">
        Loading account permissions...
      </div>
    );
  }

  // Distinguish authentication/API errors from insufficient permissions.
  if (error) {
    return (
      <div className="space-y-2 p-6">
        <h1 className="text-2xl font-bold">
          Unable to verify permissions
        </h1>

        <p className="text-muted-foreground">
          Please try refreshing the page.
        </p>
      </div>
    );
  }

  // Only administrators can access detection-rule management.
  if (!canManageRules(currentUser?.role)) {
    return (
      <div className="space-y-2 p-6">
        <h1 className="text-2xl font-bold">
          Access Denied
        </h1>

        <p className="text-muted-foreground">
          Only administrators can manage detection rules.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
          Detection Rules
        </h1>

        <p className="mt-1 text-muted-foreground">
          Manage the detection rules used to identify suspicious
          security activity.
        </p>
      </div>

      <DetectionRulesManager />
    </div>
  );
}