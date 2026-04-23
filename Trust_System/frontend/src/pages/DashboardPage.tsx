import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { useAuth } from "../app/App";
import MetricCard from "../components/MetricCard";
import SectionCard from "../components/SectionCard";
import StatusPill from "../components/StatusPill";
import { buildAuditEntries } from "../services/audit";
import { incidentsApi, reportsApi, usersApi } from "../services/api";


export default function DashboardPage() {
  const { user } = useAuth();
  const canManageQueues = user?.role === "admin" || user?.role === "moderator";

  const usersQuery = useQuery({
    queryKey: ["users", "dashboard"],
    queryFn: () => usersApi.list(100, 0),
    enabled: canManageQueues,
  });
  const reportsQuery = useQuery({
    queryKey: ["reports", "dashboard"],
    queryFn: () => reportsApi.list({ limit: 100 }),
    enabled: canManageQueues,
  });
  const incidentsQuery = useQuery({
    queryKey: ["incidents", "dashboard"],
    queryFn: () => incidentsApi.list(100, 0),
    enabled: canManageQueues,
  });

  if (!user) {
    return null;
  }

  if (!canManageQueues) {
    return (
      <div className="page-grid">
        <SectionCard
          title="Personal workspace"
          eyebrow="Dashboard"
          description="Your account can submit reports and track assigned permissions, but queue visibility is reserved for moderators and admins."
        >
          <div className="metric-grid">
            <MetricCard label="Current role" value={user.role} detail="Role-based access is active." tone="accent" />
            <MetricCard
              label="Account status"
              value={user.is_active ? "Active" : "Inactive"}
              detail="Session is controlled by the JWT-authenticated backend."
              tone={user.is_active ? "success" : "warning"}
            />
          </div>

          <div className="cta-strip">
            <p>Need to file a new moderation case or content concern?</p>
            <Link className="button button--primary" to="/reports">
              Open report intake
            </Link>
          </div>
        </SectionCard>
      </div>
    );
  }

  const users = usersQuery.data ?? [];
  const reports = reportsQuery.data ?? [];
  const incidents = incidentsQuery.data ?? [];
  const auditEntries = buildAuditEntries(users, reports, incidents).slice(0, 6);

  return (
    <div className="page-grid">
      <section className="metric-grid">
        <MetricCard
          label="Active users"
          value={users.filter((entry) => entry.is_active).length}
          detail="Accounts currently enabled for platform activity."
          tone="success"
        />
        <MetricCard
          label="Open reports"
          value={reports.filter((entry) => entry.status === "pending").length}
          detail="Pending moderation items that still need a decision."
          tone="warning"
        />
        <MetricCard
          label="Escalated incidents"
          value={incidents.filter((entry) => entry.severity === "critical").length}
          detail="Critical incidents surfaced from the moderation stream."
          tone="critical"
        />
        <MetricCard
          label="Review volume"
          value={reports.length}
          detail="Reports currently available through the shared API."
          tone="accent"
        />
      </section>

      <div className="split-grid">
        <SectionCard
          title="Priority queue"
          eyebrow="Dashboard"
          description="The most recent incident and report activity across the moderation workspace."
        >
          <div className="stack-list">
            {incidents.slice(0, 4).map((incident) => (
              <article className="list-row" key={incident.id}>
                <div>
                  <strong>{incident.subject}</strong>
                  <p>{incident.category ?? "Uncategorized"} incident pipeline</p>
                </div>
                <div className="row-meta">
                  <StatusPill value={incident.severity} variant="severity" />
                  <StatusPill value={incident.status} />
                </div>
              </article>
            ))}
            {incidents.length === 0 ? (
              <p className="empty-copy">No incidents have been derived from the current report set.</p>
            ) : null}
          </div>
        </SectionCard>

        <SectionCard
          title="Audit pulse"
          eyebrow="Latest changes"
          description="A derived operational timeline built from users, reports, and incidents."
          actions={
            <Link className="button button--ghost" to="/audit-logs">
              Open full audit view
            </Link>
          }
        >
          <div className="timeline">
            {auditEntries.map((entry) => (
              <article className="timeline-row" key={entry.id}>
                <div className={`timeline-dot timeline-dot--${entry.tone}`} />
                <div>
                  <strong>{entry.title}</strong>
                  <p>{entry.detail}</p>
                  <span>{new Date(entry.timestamp).toLocaleString()}</span>
                </div>
              </article>
            ))}
          </div>
        </SectionCard>
      </div>
    </div>
  );
}
