import type { AuditEntry, Incident, Report, User } from "../types/api";


export function buildAuditEntries(
  users: User[],
  reports: Report[],
  incidents: Incident[]
): AuditEntry[] {
  const userEntries: AuditEntry[] = users.map((user) => ({
    id: `user-${user.id}`,
    title: `User profile updated for ${user.full_name}`,
    detail: `${user.email} is currently marked as ${user.is_active ? "active" : "inactive"} with ${user.role} access.`,
    timestamp: user.updated_at,
    source: "Users",
    tone: user.is_active ? "success" : "warning",
  }));

  const reportEntries: AuditEntry[] = reports.map((report) => ({
    id: `report-${report.id}`,
    title: `Report ${report.subject} is ${report.status}`,
    detail: report.category
      ? `Category ${report.category} was logged with status ${report.status}.`
      : `Status changed to ${report.status}.`,
    timestamp: report.updated_at,
    source: "Reports",
    tone:
      report.status === "escalated"
        ? "critical"
        : report.status === "pending"
          ? "warning"
          : "success",
  }));

  const incidentEntries: AuditEntry[] = incidents.map((incident) => ({
    id: `incident-${incident.id}`,
    title: `Incident ${incident.subject} is ${incident.severity}`,
    detail: `Derived from report ${incident.report_id.slice(0, 8)} with ${incident.status} status.`,
    timestamp: incident.updated_at,
    source: "Incidents",
    tone: incident.severity === "critical" ? "critical" : "warning",
  }));

  return [...incidentEntries, ...reportEntries, ...userEntries].sort(
    (left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime()
  );
}
