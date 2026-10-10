import { api } from "@/services/api";

import type {
  DetectionRule,
  DetectionRuleUpdate,
} from "@/types/detection-rule";

/**
 * Retrieve all persisted detection rule configurations.
 *
 * The backend restricts this endpoint to administrators.
 */
export async function getDetectionRules(): Promise<
  DetectionRule[]
> {
  const response = await api.get<DetectionRule[]>(
    "/detection-rules",
  );

  return response.data;
}

/**
 * Update an existing detection rule.
 *
 * Only the supplied configuration fields are changed.
 * The backend validates parameters and writes an audit record.
 */
export async function updateDetectionRule(
  ruleName: string,
  changes: DetectionRuleUpdate,
): Promise<DetectionRule> {
  const response = await api.patch<DetectionRule>(
    `/detection-rules/${encodeURIComponent(ruleName)}`,
    changes,
  );

  return response.data;
}