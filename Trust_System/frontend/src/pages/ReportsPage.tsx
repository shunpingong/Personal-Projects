import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "../app/App";
import SectionCard from "../components/SectionCard";
import StatusPill from "../components/StatusPill";
import { ApiError, reportsApi } from "../services/api";
import type { ReportStatus } from "../types/api";


const reportFilters: Array<ReportStatus | "all"> = ["all", "pending", "reviewed", "escalated"];

export default function ReportsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState<ReportStatus | "all">("all");
  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [createMessage, setCreateMessage] = useState<string | null>(null);
  const [createError, setCreateError] = useState<string | null>(null);

  const canModerate = user?.role === "admin" || user?.role === "moderator";

  const reportsQuery = useQuery({
    queryKey: ["reports", filter],
    queryFn: () => reportsApi.list({ status: filter }),
    enabled: canModerate,
  });

  const createReportMutation = useMutation({
    mutationFn: reportsApi.create,
    onSuccess: () => {
      setSubject("");
      setCategory("");
      setDescription("");
      setCreateError(null);
      setCreateMessage("Report submitted successfully.");
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
    onError: (error) => {
      setCreateMessage(null);
      setCreateError(error instanceof ApiError ? error.message : "Unable to submit the report.");
    },
  });

  const updateStatusMutation = useMutation({
    mutationFn: ({ reportId, status }: { reportId: string; status: ReportStatus }) =>
      reportsApi.updateStatus(reportId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
    },
  });

  const summary = useMemo(() => {
    const reports = reportsQuery.data ?? [];
    return {
      total: reports.length,
      pending: reports.filter((entry) => entry.status === "pending").length,
      escalated: reports.filter((entry) => entry.status === "escalated").length,
    };
  }, [reportsQuery.data]);

  if (!user) {
    return null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await createReportMutation.mutateAsync({
      subject,
      category,
      description,
    });
  }

  if (!canModerate) {
    return (
      <div className="page-grid">
        <SectionCard
          title="Report intake"
          eyebrow="Reports"
          description="Standard users can submit new cases. Queue review and status changes stay with moderators and admins."
        >
          <form className="form-grid" onSubmit={handleSubmit}>
            <label className="field">
              <span>Subject</span>
              <input
                value={subject}
                onChange={(event) => setSubject(event.target.value)}
                required
                placeholder="Abusive content, account takeover, policy breach"
              />
            </label>

            <label className="field">
              <span>Category</span>
              <input
                value={category}
                onChange={(event) => setCategory(event.target.value)}
                placeholder="harassment, fraud, account abuse"
              />
            </label>

            <label className="field field--full">
              <span>Description</span>
              <textarea
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                required
                rows={6}
                placeholder="Describe what happened and why it needs trust and safety review."
              />
            </label>

            {createMessage ? <p className="form-success">{createMessage}</p> : null}
            {createError ? <p className="form-error">{createError}</p> : null}

            <button
              type="submit"
              className="button button--primary"
              disabled={createReportMutation.isPending}
            >
              {createReportMutation.isPending ? "Submitting..." : "Submit report"}
            </button>
          </form>
        </SectionCard>
      </div>
    );
  }

  return (
    <div className="page-grid">
      <SectionCard
        title="Moderation report queue"
        eyebrow="Reports"
        description="Review, escalate, and resolve report intake without leaving the workspace."
        actions={
          <div className="button-group">
            {reportFilters.map((entry) => (
              <button
                key={entry}
                type="button"
                className={entry === filter ? "button button--primary" : "button button--ghost"}
                onClick={() => setFilter(entry)}
              >
                {entry}
              </button>
            ))}
          </div>
        }
      >
        <div className="metric-strip">
          <div>
            <span>Total</span>
            <strong>{summary.total}</strong>
          </div>
          <div>
            <span>Pending</span>
            <strong>{summary.pending}</strong>
          </div>
          <div>
            <span>Escalated</span>
            <strong>{summary.escalated}</strong>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Subject</th>
                <th>Category</th>
                <th>Status</th>
                <th>Reporter</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {(reportsQuery.data ?? []).map((report) => (
                <tr key={report.id}>
                  <td>
                    <strong>{report.subject}</strong>
                    <p>{report.description}</p>
                  </td>
                  <td>{report.category ?? "Uncategorized"}</td>
                  <td>
                    <StatusPill value={report.status} />
                  </td>
                  <td>{report.reporter_id ? report.reporter_id.slice(0, 8) : "Unknown"}</td>
                  <td>{new Date(report.created_at).toLocaleString()}</td>
                  <td>
                    <div className="table-actions">
                      <button
                        type="button"
                        className="button button--ghost"
                        onClick={() =>
                          updateStatusMutation.mutate({
                            reportId: report.id,
                            status: "reviewed",
                          })
                        }
                        disabled={updateStatusMutation.isPending}
                      >
                        Mark reviewed
                      </button>
                      <button
                        type="button"
                        className="button button--ghost"
                        onClick={() =>
                          updateStatusMutation.mutate({
                            reportId: report.id,
                            status: "escalated",
                          })
                        }
                        disabled={updateStatusMutation.isPending}
                      >
                        Escalate
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {!reportsQuery.isLoading && (reportsQuery.data ?? []).length === 0 ? (
            <p className="empty-copy">No reports match the current filter.</p>
          ) : null}
        </div>
      </SectionCard>
    </div>
  );
}
