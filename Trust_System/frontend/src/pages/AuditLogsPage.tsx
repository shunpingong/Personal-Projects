import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../app/App";
import SectionCard from "../components/SectionCard";
import StatusPill from "../components/StatusPill";
import { buildAuditEntries } from "../services/audit";
import { incidentsApi, reportsApi, usersApi } from "../services/api";


export default function AuditLogsPage() {
  const { user } = useAuth();
  const canViewAudit = user?.role === "admin" || user?.role === "moderator";

  const usersQuery = useQuery({
    queryKey: ["audit", "users"],
    queryFn: () => usersApi.list(100, 0),
    enabled: canViewAudit,
  });
  const reportsQuery = useQuery({
    queryKey: ["audit", "reports"],
    queryFn: () => reportsApi.list({ limit: 100 }),
    enabled: canViewAudit,
  });
  const incidentsQuery = useQuery({
    queryKey: ["audit", "incidents"],
    queryFn: () => incidentsApi.list(100, 0),
    enabled: canViewAudit,
  });

  const entries = useMemo(
    () =>
      buildAuditEntries(
        usersQuery.data ?? [],
        reportsQuery.data ?? [],
        incidentsQuery.data ?? []
      ),
    [incidentsQuery.data, reportsQuery.data, usersQuery.data]
  );

  if (!canViewAudit) {
    return (
      <div className="page-grid">
        <SectionCard
          title="Audit logs"
          eyebrow="Audit"
          description="The audit view is reserved for moderators and admins."
        >
          <p className="empty-copy">You do not currently have permission to inspect this timeline.</p>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-grid">
      <SectionCard
        title="Derived audit timeline"
        eyebrow="Audit"
        description="This page combines user, report, and incident activity into one operational timeline without requiring a separate audit microservice."
      >
        <div className="timeline">
          {entries.map((entry) => (
            <article className="timeline-row timeline-row--full" key={entry.id}>
              <div className={`timeline-dot timeline-dot--${entry.tone}`} />
              <div className="timeline-row__content">
                <div className="timeline-row__header">
                  <strong>{entry.title}</strong>
                  <StatusPill value={entry.source} variant="tone" />
                </div>
                <p>{entry.detail}</p>
                <span>{new Date(entry.timestamp).toLocaleString()}</span>
              </div>
            </article>
          ))}

          {entries.length === 0 ? (
            <p className="empty-copy">No audit entries are available from the current dataset.</p>
          ) : null}
        </div>
      </SectionCard>
    </div>
  );
}
