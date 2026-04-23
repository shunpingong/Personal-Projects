import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { useAuth } from "../app/App";
import MetricCard from "../components/MetricCard";
import SectionCard from "../components/SectionCard";
import StatusPill from "../components/StatusPill";
import { incidentsApi } from "../services/api";


export default function IncidentsPage() {
  const { user } = useAuth();
  const canViewIncidents = user?.role === "admin" || user?.role === "moderator";

  const incidentsQuery = useQuery({
    queryKey: ["incidents", "list"],
    queryFn: () => incidentsApi.list(100, 0),
    enabled: canViewIncidents,
  });

  const summary = useMemo(() => {
    const incidents = incidentsQuery.data ?? [];
    return {
      total: incidents.length,
      critical: incidents.filter((entry) => entry.severity === "critical").length,
      high: incidents.filter((entry) => entry.severity === "high").length,
    };
  }, [incidentsQuery.data]);

  if (!canViewIncidents) {
    return (
      <div className="page-grid">
        <SectionCard
          title="Incident queue"
          eyebrow="Incidents"
          description="Incident visibility is derived for moderators and admins from the shared report stream."
        >
          <p className="empty-copy">Your role does not include access to the incident queue.</p>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-grid">
      <section className="metric-grid">
        <MetricCard
          label="Incident volume"
          value={summary.total}
          detail="Derived from the backend incident compatibility endpoint."
          tone="accent"
        />
        <MetricCard
          label="Critical"
          value={summary.critical}
          detail="Escalated incidents needing rapid intervention."
          tone="critical"
        />
        <MetricCard
          label="High severity"
          value={summary.high}
          detail="Incidents flagged by category risk or escalation state."
          tone="warning"
        />
      </section>

      <SectionCard
        title="Incident queue"
        eyebrow="Incidents"
        description="Reports with incident-level severity, ordered by the most recent update."
      >
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Category</th>
                <th>Source report</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {(incidentsQuery.data ?? []).map((incident) => (
                <tr key={incident.id}>
                  <td>
                    <strong>{incident.subject}</strong>
                    <p>{incident.description}</p>
                  </td>
                  <td>
                    <StatusPill value={incident.severity} variant="severity" />
                  </td>
                  <td>
                    <StatusPill value={incident.status} />
                  </td>
                  <td>{incident.category ?? "Uncategorized"}</td>
                  <td>{incident.report_id.slice(0, 8)}</td>
                  <td>{new Date(incident.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {!incidentsQuery.isLoading && (incidentsQuery.data ?? []).length === 0 ? (
            <p className="empty-copy">No current incidents match the derived severity rules.</p>
          ) : null}
        </div>
      </SectionCard>
    </div>
  );
}
