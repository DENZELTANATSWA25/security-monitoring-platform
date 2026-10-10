"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getDetectionRules,
  updateDetectionRule,
} from "@/services/detection-rules.service";

import type {
  DetectionRuleUpdate,
} from "@/types/detection-rule";

/**
 * Fetch the registered detection rules.
 */
export function useDetectionRules(
  enabled = true,
) {
  return useQuery({
    queryKey: ["detection-rules"],
    queryFn: getDetectionRules,
    enabled,
    refetchOnWindowFocus: true,
  });
}

/**
 * Update rule configuration and refresh the rule list.
 */
export function useUpdateDetectionRule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      ruleName,
      changes,
    }: {
      ruleName: string;
      changes: DetectionRuleUpdate;
    }) =>
      updateDetectionRule(ruleName, changes),

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: ["detection-rules"],
      });
    },
  });
}