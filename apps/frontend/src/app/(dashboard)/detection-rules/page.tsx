"use client";

import DetectionRulesManager from "@/components/detection-rules/detection-rules-manager";

export default function DetectionRulesPage() {
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