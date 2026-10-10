"use client";

import axios from "axios";
import { useState } from "react";

import { useCurrentUser } from "@/hooks/use-users";
import {
  useTelemetrySources,
  useTelemetrySourceStatuses,
  useRefreshTelemetrySources,
} from "@/hooks/use-telemetry-sources";

import {
  createTelemetrySource,
  revokeTelemetrySource,
  rotateTelemetrySourceCredential,
} from "@/services/telemetry-source.service";

import {
  canManageTelemetrySources,
  canViewTelemetryHealth,
} from "@/lib/permissions";

import type {
  TelemetrySource,
  TelemetrySourceCredentialResponse,
} from "@/types/telemetry-source";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }
  }

  return "The telemetry operation could not be completed.";
}

function formatDate(value: string | null): string {
  if (!value) return "Never";

  const date = new Date(value);

  return Number.isNaN(date.getTime())
    ? "Unknown"
    : date.toLocaleString();
}

type CredentialDisplay = {
  sourceName: string;
  credential: string;
  operation: "registration" | "rotation";
};

function CredentialNotice({
  credential,
  onDismiss,
}: {
  credential: CredentialDisplay;
  onDismiss: () => void;
}) {
  const [acknowledged, setAcknowledged] = useState(false);

  return (
    <Card className="border-amber-500">
      <CardHeader>
        <CardTitle>One-time telemetry credential</CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        <p className="text-sm">
          {credential.operation === "registration"
            ? "Source registered successfully."
            : "Credential rotated successfully."}
          {" "}
          Copy the credential for{" "}
          <strong>{credential.sourceName}</strong>.
          It cannot be retrieved again after dismissal.
        </p>

        <div className="rounded-lg border bg-muted p-3">
          <code className="break-all text-sm">
            {credential.credential}
          </code>
        </div>

        <label className="flex items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={acknowledged}
            onChange={(event) =>
              setAcknowledged(event.target.checked)
            }
          />

          <span>
            I have securely saved this credential and understand
            that it cannot be retrieved again.
          </span>
        </label>

        <Button
          disabled={!acknowledged}
          onClick={onDismiss}
        >
          Dismiss credential
        </Button>
      </CardContent>
    </Card>
  );
}

export default function TelemetrySourcesManager() {
  const { data: currentUser, isLoading: isLoadingUser } =
    useCurrentUser();

  const canManage = canManageTelemetrySources(
    currentUser?.role,
  );

  const canView = canViewTelemetryHealth(
    currentUser?.role,
  );

  const {
    data: sources = [],
    isLoading: isLoadingSources,
    error: sourcesError,
  } = useTelemetrySources(canManage);

  const {
    data: statuses = [],
    isLoading: isLoadingStatuses,
    error: statusesError,
    refetch: refetchStatuses,
  } = useTelemetrySourceStatuses(canView);

  const refreshSources = useRefreshTelemetrySources();

  const [name, setName] = useState("");
  const [sourceType, setSourceType] = useState("");

  const [credential, setCredential] =
    useState<CredentialDisplay | null>(null);

  const [busySourceId, setBusySourceId] =
    useState<number | null>(null);

  const [isRegistering, setIsRegistering] =
    useState(false);

  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function registerSource() {
    const trimmedName = name.trim();
    const trimmedType = sourceType.trim();

    if (!trimmedName || !trimmedType) {
      setError("Source name and type are required.");
      return;
    }

    if (trimmedName.length > 255 || trimmedType.length > 255) {
      setError("Name and source type must not exceed 255 characters.");
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      setIsRegistering(true);

      const result: TelemetrySourceCredentialResponse =
        await createTelemetrySource({
          name: trimmedName,
          source_type: trimmedType,
        });

      setCredential({
        sourceName: result.name,
        credential: result.credential,
        operation: "registration",
      });

      setName("");
      setSourceType("");

      await refreshSources();
    } catch (error) {
      setError(getErrorMessage(error));
    } finally {
      setIsRegistering(false);
    }
  }

  async function rotateCredential(source: TelemetrySource) {
    if (
      !window.confirm(
        `Rotate the credential for "${source.name}"?\n\n` +
          "The existing credential will stop working immediately.",
      )
    ) {
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      setBusySourceId(source.id);

      const result =
        await rotateTelemetrySourceCredential(source.id);

      setCredential({
        sourceName: result.name,
        credential: result.credential,
        operation: "rotation",
      });

      await refreshSources();
    } catch (error) {
      setError(getErrorMessage(error));
    } finally {
      setBusySourceId(null);
    }
  }

  async function revokeSource(source: TelemetrySource) {
    if (
      !window.confirm(
        `Revoke "${source.name}"?\n\n` +
          "This disables the source and cannot be undone " +
          "through the current API.",
      )
    ) {
      return;
    }

    setError(null);
    setSuccess(null);

    try {
      setBusySourceId(source.id);

      await revokeTelemetrySource(source.id);

      setSuccess(`Telemetry source "${source.name}" revoked.`);

      await refreshSources();
    } catch (error) {
      setError(getErrorMessage(error));
    } finally {
      setBusySourceId(null);
    }
  }

  if (isLoadingUser) {
    return <p>Loading permissions...</p>;
  }

  if (!canView) {
    return (
      <p className="text-destructive">
        You do not have permission to view telemetry sources.
      </p>
    );
  }

  if (isLoadingStatuses || (canManage && isLoadingSources)) {
    return <p>Loading telemetry sources...</p>;
  }

  if (statusesError || (canManage && sourcesError)) {
    return (
      <div className="space-y-3">
        <p className="text-destructive">
          Unable to load telemetry source information.
        </p>

        <Button
          variant="outline"
          onClick={() => {
            void refetchStatuses();
            void refreshSources();
          }}
        >
          Retry
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {credential && (
        <CredentialNotice
          credential={credential}
          onDismiss={() => setCredential(null)}
        />
      )}

      {canManage && !credential && (
        <Card>
          <CardHeader>
            <CardTitle>Register telemetry source</CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <Input
                placeholder="Source name"
                value={name}
                maxLength={255}
                onChange={(event) => setName(event.target.value)}
              />

              <Input
                placeholder="Source type (e.g. firewall)"
                value={sourceType}
                maxLength={255}
                onChange={(event) => setSourceType(event.target.value)}
              />
            </div>

            <Button
              onClick={registerSource}
              disabled={isRegistering}
            >
              {isRegistering ? "Registering..." : "Register source"}
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Source health</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          <Button
            variant="outline"
            onClick={() => void refetchStatuses()}
          >
            Refresh health
          </Button>

          {statuses.length === 0 ? (
            <p className="text-muted-foreground">
              No telemetry sources registered.
            </p>
          ) : (
            <div className="space-y-3">
              {statuses.map((status) => (
                <div
                  key={status.id}
                  className="rounded-lg border p-4"
                >
                  <div className="flex flex-wrap justify-between gap-3">
                    <div>
                      <h3 className="font-semibold">{status.name}</h3>

                      <p className="text-sm text-muted-foreground">
                        {status.source_type}
                      </p>
                    </div>

                    <Badge variant="outline">
                      {status.health_status.replace("_", " ")}
                    </Badge>
                  </div>

                  <div className="mt-4 grid gap-3 text-sm sm:grid-cols-3">
                    <div>
                      <p className="text-muted-foreground">
                        Events (24h)
                      </p>
                      <p className="font-semibold">
                        {status.events_24h}
                      </p>
                    </div>

                    <div>
                      <p className="text-muted-foreground">
                        Last seen
                      </p>
                      <p>{formatDate(status.last_seen_at)}</p>
                    </div>

                    <div>
                      <p className="text-muted-foreground">
                        Last event
                      </p>
                      <p>{formatDate(status.last_event_at)}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {canManage && (
        <Card>
          <CardHeader>
            <CardTitle>Registered sources</CardTitle>
          </CardHeader>

          <CardContent className="space-y-4">
            {sources.length === 0 ? (
              <p className="text-muted-foreground">
                No registered sources.
              </p>
            ) : (
              sources.map((source) => (
                <div
                  key={source.id}
                  className="rounded-lg border p-4"
                >
                  <div className="flex flex-wrap justify-between gap-3">
                    <div>
                      <h3 className="font-semibold">{source.name}</h3>

                      <p className="text-sm text-muted-foreground">
                        {source.source_type}
                      </p>

                      <p className="mt-2 font-mono text-xs">
                        Key ID: {source.key_id}
                      </p>
                    </div>

                    <Badge
                      variant={source.is_active ? "default" : "outline"}
                    >
                      {source.is_active ? "Active" : "Revoked"}
                    </Badge>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-3">
                    <Button
                      variant="outline"
                      disabled={
                        !source.is_active ||
                        busySourceId !== null ||
                        credential !== null
                      }
                      onClick={() => rotateCredential(source)}
                    >
                      Rotate credential
                    </Button>

                    <Button
                      variant="destructive"
                      disabled={
                        !source.is_active ||
                        busySourceId !== null ||
                        credential !== null
                      }
                      onClick={() => revokeSource(source)}
                    >
                      Revoke source
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {error && (
        <p role="alert" className="text-sm text-destructive">
          {error}
        </p>
      )}

      {success && (
        <p role="status" className="text-sm text-green-700">
          {success}
        </p>
      )}
    </div>
  );
}