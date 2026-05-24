export type UserRole = "admin" | "reviewer" | "readonly";

export type SystemStatus =
  | "draft"
  | "under_review"
  | "compliant"
  | "non_compliant"
  | "exempted";

export type RiskCategory =
  | "prohibited"
  | "high_risk"
  | "limited_risk"
  | "minimal_risk";

export type ModelCardStatus = "draft" | "published" | "archived";

export type ScanSourceType = "file" | "text" | "database_sample";
export type ScanStatus = "pending" | "running" | "completed" | "failed";
export type PIIScanRiskLevel = "critical" | "high" | "medium" | "low" | "none";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AISystem {
  id: string;
  name: string;
  description: string | null;
  version: string | null;
  owner_team: string | null;
  tech_stack: string[] | null;
  deployment_env: string | null;
  use_case: string | null;
  data_types: string[] | null;
  is_autonomous: boolean;
  affects_persons: boolean;
  status: SystemStatus;
  current_risk_category: RiskCategory | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface AISystemList {
  items: AISystem[];
  total: number;
  page: number;
  per_page: number;
}

export interface RequiredAction {
  article: string;
  obligation: string;
  deadline: string;
}

export interface RiskAssessment {
  id: string;
  ai_system_id: string;
  assessed_by: string | null;
  total_score: number;
  risk_category: RiskCategory;
  justification: string | null;
  ai_act_articles: string[] | null;
  required_actions: RequiredAction[] | null;
  valid_until: string | null;
  created_at: string;
}

export interface PIIFinding {
  entity_type: string;
  start: number;
  end: number;
  score: number;
  context?: string;
}

export interface PIIScan {
  id: string;
  ai_system_id: string | null;
  scanned_by: string | null;
  source_type: ScanSourceType;
  source_name: string | null;
  source_hash: string | null;
  total_items: number;
  pii_found: boolean;
  findings: PIIFinding[];
  entity_summary: Record<string, number> | null;
  confidence_threshold: number;
  status: ScanStatus;
  risk_level: PIIScanRiskLevel | null;
  recommendations: string[] | null;
  created_at: string;
}

export interface AuditLog {
  id: string;
  actor_id: string | null;
  actor_email: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  input_payload: Record<string, unknown> | null;
  output_summary: Record<string, unknown> | null;
  payload_hash: string;
  ip_address: string | null;
  created_at: string;
}

export interface DashboardSummary {
  total_systems: number;
  compliant: number;
  under_review: number;
  non_compliant: number;
  not_assessed: number;
  risk_distribution: Record<RiskCategory, number>;
  compliance_rate: number;
}

export interface ApiError {
  error: string;
  status_code: number;
}
