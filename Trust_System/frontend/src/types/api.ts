export type UserRole = "admin" | "moderator" | "user";
export type ReportStatus = "pending" | "reviewed" | "escalated";
export type IncidentSeverity = "medium" | "high" | "critical";
export type AuditTone = "neutral" | "success" | "warning" | "critical";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_token_expires_in: number;
  refresh_token_expires_in: number;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  full_name: string;
  password: string;
}

export interface CreateUserPayload {
  email: string;
  full_name: string;
  password: string;
  role: UserRole;
  is_active: boolean;
}

export interface UpdateUserPayload {
  email?: string;
  full_name?: string;
  password?: string;
  role?: UserRole;
  is_active?: boolean;
}

export interface Report {
  id: string;
  subject: string;
  category: string | null;
  description: string;
  status: ReportStatus;
  reporter_id: string | null;
  reviewed_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateReportPayload {
  subject: string;
  category: string;
  description: string;
}

export interface Incident {
  id: string;
  report_id: string;
  subject: string;
  category: string | null;
  description: string;
  status: ReportStatus;
  severity: IncidentSeverity;
  reporter_id: string | null;
  reviewed_by_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditEntry {
  id: string;
  title: string;
  detail: string;
  timestamp: string;
  source: string;
  tone: AuditTone;
}
