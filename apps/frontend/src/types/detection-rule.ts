export interface DetectionRule {
  id: number;
  rule_name: string;
  display_name: string;
  description: string;
  is_enabled: boolean;
  parameters: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DetectionRuleUpdate {
  is_enabled?: boolean;
  parameters?: Record<string, unknown>;
}