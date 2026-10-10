"use client";

import TelemetrySourcesManager from "@/components/telemetry/telemetry-sources-manager";

export default function TelemetrySourcesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">
          Telemetry Sources
        </h1>

        <p className="mt-1 text-muted-foreground">
          Register external telemetry producers, monitor source
          health and manage credentials.
        </p>
      </div>

      <TelemetrySourcesManager />
    </div>
  );
}