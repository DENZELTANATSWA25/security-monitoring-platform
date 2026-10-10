"use client";

import axios from "axios";
import { useState } from "react";

import {
  useDetectionRules,
  useUpdateDetectionRule,
} from "@/hooks/use-detection-rules";

import type { DetectionRule } from "@/types/detection-rule";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type ParameterValues = Record<string, string>;

type ParameterDefinition = {
  key: string;
  label: string;
  minimum: number;
  exclusiveMinimum?: boolean;
  integer?: boolean;
};

const PARAMETER_DEFINITIONS: Record<
  string,
  ParameterDefinition[]
> = {
  failed_attempts_threshold: [
    {
      key: "failed_attempts_threshold",
      label: "Failed attempts threshold",
      minimum: 1,
      integer: true,
    },
  ],
  event_threshold: [
    {
      key: "event_threshold",
      label: "Event threshold",
      minimum: 1,
      integer: true,
    },
    {
      key: "window_minutes",
      label: "Window (minutes)",
      minimum: 1,
      integer: true,
    },
  ],
  max_travel_speed_kmh: [
    {
      key: "max_travel_speed_kmh",
      label: "Maximum travel speed (km/h)",
      minimum: 0,
      exclusiveMinimum: true,
    },
    {
      key: "min_distance_km",
      label: "Minimum distance (km)",
      minimum: 0,
    },
  ],
};

function getParameterDefinitions(
  rule: DetectionRule,
): ParameterDefinition[] {
  if ("failed_attempts_threshold" in rule.parameters) {
    return PARAMETER_DEFINITIONS.failed_attempts_threshold;
  }

  if ("event_threshold" in rule.parameters) {
    return PARAMETER_DEFINITIONS.event_threshold;
  }

  if ("max_travel_speed_kmh" in rule.parameters) {
    return PARAMETER_DEFINITIONS.max_travel_speed_kmh;
  }

  return [];
}

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item?.msg === "string"
            ? item.msg
            : "Invalid rule configuration",
        )
        .join("; ");
    }
  }

  return "Unable to update the detection rule.";
}

function RuleCard({
  rule,
}: {
  rule: DetectionRule;
}) {
  const updateRule = useUpdateDetectionRule();

  const definitions = getParameterDefinitions(rule);

  const [editing, setEditing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [values, setValues] = useState<ParameterValues>(
    () =>
      Object.fromEntries(
        Object.entries(rule.parameters).map(([key, value]) => [
          key,
          String(value),
        ]),
      ),
  );

  function resetValues() {
    setValues(
      Object.fromEntries(
        Object.entries(rule.parameters).map(([key, value]) => [
          key,
          String(value),
        ]),
      ),
    );
  }

  async function toggleEnabled() {
    setError(null);
    setSuccess(null);

    try {
      await updateRule.mutateAsync({
        ruleName: rule.rule_name,
        changes: {
          is_enabled: !rule.is_enabled,
        },
      });

      setSuccess(
        rule.is_enabled
          ? "Rule disabled successfully."
          : "Rule enabled successfully.",
      );
    } catch (error) {
      setError(getErrorMessage(error));
    }
  }

  async function saveParameters() {
    setError(null);
    setSuccess(null);

    const parameters: Record<string, number> = {};

    for (const definition of definitions) {
      const rawValue = values[definition.key]?.trim();

      if (!rawValue) {
        setError(`${definition.label} is required.`);
        return;
      }

      const value = Number(rawValue);

      if (!Number.isFinite(value)) {
        setError(`${definition.label} must be a number.`);
        return;
      }

      if (definition.integer && !Number.isInteger(value)) {
        setError(`${definition.label} must be an integer.`);
        return;
      }

      if (
        definition.exclusiveMinimum
          ? value <= definition.minimum
          : value < definition.minimum
      ) {
        setError(
          `${definition.label} must be ${
            definition.exclusiveMinimum ? "greater than" : "at least"
          } ${definition.minimum}.`,
        );
        return;
      }

      parameters[definition.key] = value;
    }

    try {
      await updateRule.mutateAsync({
        ruleName: rule.rule_name,
        changes: { parameters },
      });

      setEditing(false);
      setSuccess("Rule parameters updated successfully.");
    } catch (error) {
      setError(getErrorMessage(error));
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <CardTitle>{rule.display_name}</CardTitle>

            <p className="text-sm text-muted-foreground">
              {rule.description}
            </p>

            <p className="font-mono text-xs text-muted-foreground">
              {rule.rule_name}
            </p>
          </div>

          <Badge variant={rule.is_enabled ? "default" : "outline"}>
            {rule.is_enabled ? "Enabled" : "Disabled"}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-5">
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant={rule.is_enabled ? "outline" : "default"}
            disabled={updateRule.isPending}
            onClick={toggleEnabled}
          >
            {updateRule.isPending
              ? "Saving..."
              : rule.is_enabled
                ? "Disable rule"
                : "Enable rule"}
          </Button>

          {definitions.length > 0 && !editing && (
            <Button
              variant="outline"
              disabled={updateRule.isPending}
              onClick={() => {
                resetValues();
                setError(null);
                setSuccess(null);
                setEditing(true);
              }}
            >
              Edit parameters
            </Button>
          )}
        </div>

        {definitions.length === 0 ? (
            <div className="space-y-2">
                {Object.keys(rule.parameters).length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                        This rule has no configurable parameters.
                    </p>
                ) : (
                  <>
                    <p className="text-sm text-muted-foreground">
                        This rule contains parameters that are not supported
                        by the current editor.
                    </p>

                    <pre className="overflow-x-auto rounded-1g border p-3 text-xs">
                        {JSON.stringify(rule.parameters, null, 2)}
                    </pre>
                  </>
                )}
            </div>
        ) : editing ? (
          <div className="space-y-4 rounded-lg border p-4">
            <h3 className="font-semibold">Rule parameters</h3>

            <div className="grid gap-4 sm:grid-cols-2">
              {definitions.map((definition) => (
                <label
                  key={definition.key}
                  className="space-y-2 text-sm"
                >
                  <span>{definition.label}</span>

                  <Input
                    type="number"
                    step={definition.integer ? "1" : "any"}
                    min={definition.minimum}
                    value={values[definition.key] ?? ""}
                    onChange={(event) =>
                      setValues((previous) => ({
                        ...previous,
                        [definition.key]: event.target.value,
                      }))
                    }
                    disabled={updateRule.isPending}
                  />
                </label>
              ))}
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                disabled={updateRule.isPending}
                onClick={saveParameters}
              >
                {updateRule.isPending ? "Saving..." : "Save changes"}
              </Button>

              <Button
                variant="outline"
                disabled={updateRule.isPending}
                onClick={() => {
                  resetValues();
                  setEditing(false);
                  setError(null);
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div>
            <h3 className="mb-3 font-semibold">
              Current parameters
            </h3>

            <div className="grid gap-3 sm:grid-cols-2">
              {definitions.map((definition) => (
                <div
                  key={definition.key}
                  className="rounded-lg border p-3"
                >
                  <p className="text-sm text-muted-foreground">
                    {definition.label}
                  </p>

                  <p className="mt-1 font-semibold">
                    {String(
                      rule.parameters[definition.key] ?? "Not configured",
                    )}
                  </p>
                </div>
              ))}
            </div>
          </div>
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
      </CardContent>
    </Card>
  );
}

export default function DetectionRulesManager() {
  const {
    data: rules = [],
    isLoading,
    error,
    refetch,
    isFetching,
  } = useDetectionRules();

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          Loading detection rules...
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="space-y-3 p-6">
          <p className="text-destructive">
            Failed to load detection rules.
          </p>

          <Button variant="outline" onClick={() => refetch()}>
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {rules.length} registered detection rules
        </p>

        <Button
          variant="outline"
          disabled={isFetching}
          onClick={() => refetch()}
        >
          {isFetching ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      {rules.length === 0 ? (
        <Card>
          <CardContent className="p-6">
            No detection rules are registered.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {rules.map((rule) => (
            <RuleCard key={rule.id} rule={rule} />
          ))}
        </div>
      )}
    </div>
  );
}