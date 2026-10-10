import { api } from "@/services/api";

import type {
  TelemetrySource,
  TelemetrySourceCreate,
  TelemetrySourceCredentialResponse,
  TelemetrySourceStatus,
} from "@/types/telemetry-source";

/**
 * Retrieve registered telemetry sources.
 * Admin only.
 */
export async function getTelemetrySources(): Promise<
  TelemetrySource[]
> {
  const response = await api.get<TelemetrySource[]>(
    "/telemetry-sources",
  );

  return response.data;
}

/**
 * Retrieve operational health information.
 * Admin and analyst.
 */
export async function getTelemetrySourceStatuses(): Promise<
  TelemetrySourceStatus[]
> {
  const response = await api.get<TelemetrySourceStatus[]>(
    "/telemetry-sources/status",
  );

  return response.data;
}

/**
 * Retrieve one source.
 * Admin only.
 */
export async function getTelemetrySource(
  sourceId: number,
): Promise<TelemetrySource> {
  const response = await api.get<TelemetrySource>(
    `/telemetry-sources/${sourceId}`,
  );

  return response.data;
}

/**
 * Register a source and return its one-time credential.
 *
 * The caller must handle the credential directly.
 * Do not persist the response in a React Query cache.
 */
export async function createTelemetrySource(
  payload: TelemetrySourceCreate,
): Promise<TelemetrySourceCredentialResponse> {
  const response =
    await api.post<TelemetrySourceCredentialResponse>(
      "/telemetry-sources",
      payload,
    );

  return response.data;
}

/**
 * Rotate a source credential.
 *
 * The previous credential becomes invalid immediately
 * after the backend commits the rotation.
 */
export async function rotateTelemetrySourceCredential(
  sourceId: number,
): Promise<TelemetrySourceCredentialResponse> {
  const response =
    await api.post<TelemetrySourceCredentialResponse>(
      `/telemetry-sources/${sourceId}/rotate-credential`,
    );

  return response.data;
}

/**
 * Revoke a telemetry source.
 *
 * The current backend does not support reactivation.
 */
export async function revokeTelemetrySource(
  sourceId: number,
): Promise<TelemetrySource> {
  const response = await api.post<TelemetrySource>(
    `/telemetry-sources/${sourceId}/revoke`,
  );

  return response.data;
}