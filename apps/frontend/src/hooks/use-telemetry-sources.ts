"use client";

import {
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getTelemetrySources,
  getTelemetrySourceStatuses,
} from "@/services/telemetry-source.service";

/**
 * Administrative source listing.
 */
export function useTelemetrySources(
  enabled = true,
) {
  return useQuery({
    queryKey: ["telemetry-sources"],
    queryFn: getTelemetrySources,
    enabled,
    refetchOnWindowFocus: true,
  });
}

/**
 * Operational health monitoring.
 *
 * Health can change as events arrive, so refresh
 * automatically every 30 seconds.
 */
export function useTelemetrySourceStatuses(
  enabled = true,
) {
  return useQuery({
    queryKey: ["telemetry-source-statuses"],
    queryFn: getTelemetrySourceStatuses,
    enabled,
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
  });
}

/**
 * Refresh telemetry information after administrative changes.
 */
export function useRefreshTelemetrySources() {
  const queryClient = useQueryClient();

  return async function refreshTelemetrySources() {
    await Promise.all([
      queryClient.invalidateQueries({
        queryKey: ["telemetry-sources"],
      }),

      queryClient.invalidateQueries({
        queryKey: ["telemetry-source-statuses"],
      }),
    ]);
  };
}