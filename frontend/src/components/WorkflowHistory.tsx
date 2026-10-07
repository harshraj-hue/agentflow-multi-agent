import React, { useState } from "react";
import type { WorkflowSummary } from "../types/workflow";

interface WorkflowHistoryProps {
  workflows: WorkflowSummary[];
  onSelectWorkflow: (id: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
}

export const WorkflowHistory: React.FC<WorkflowHistoryProps> = ({
  workflows,
  onSelectWorkflow,
  onRefresh,
  isLoading,
}) => {
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState<string>("");

  const filtered = workflows.filter((w) => {
    if (filter !== "all" && w.status !== filter) return false;
    if (
      search &&
      !w.title.toLowerCase().includes(search.toLowerCase()) &&
      !w.objective.toLowerCase().includes(search.toLowerCase())
    ) {
      return false;
    }
    return true;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return <span className="status-badge badge-running"><span className="pulse-dot" />Running</span>;
      case "waiting_for_approval":
        return <span className="status-badge badge-approval"><span className="pulse-dot-amber" />Awaiting Sign-off</span>;
      case "completed":
        return <span className="status-badge badge-completed">✓ Completed</span>;
      case "failed":
        return <span className="status-badge badge-failed">✕ Failed</span>;
      case "paused":
        return <span className="status-badge badge-ready">⏸ Paused</span>;
      default:
        return <span className="status-badge badge-pending">{status}</span>;
    }
  };

  const formatDate = (isoStr: string) => {
    try {
      return new Date(isoStr).toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="history-container">
      <div className="history-header">
        <div>
          <h2 className="history-title">Workflow Execution History</h2>
          <p className="history-subtitle">
            Auditable execution logs, metrics, and deliverables across all autonomous runs.
          </p>
        </div>

        <button
          type="button"
          className="btn-secondary"
          onClick={onRefresh}
          disabled={isLoading}
        >
          {isLoading ? "Refreshing..." : "↻ Refresh"}
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="history-toolbar">
        <div className="filter-chips">
          {["all", "running", "waiting_for_approval", "completed", "failed"].map((st) => (
            <button
              key={st}
              type="button"
              className={`filter-chip ${filter === st ? "active" : ""}`}
              onClick={() => setFilter(st)}
            >
              {st === "all" ? "All Missions" : st.replace("_", " ").toUpperCase()}
            </button>
          ))}
        </div>

        <input
          type="text"
          className="search-input"
          placeholder="Search by title or objective..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Workflow Table / Grid */}
      <div className="history-list">
        {filtered.length === 0 ? (
          <div className="empty-history">
            <p className="muted">No workflows found matching your filter criteria.</p>
          </div>
        ) : (
          filtered.map((wf) => {
            const progress =
              wf.tasks_count > 0
                ? Math.round((wf.completed_tasks_count / wf.tasks_count) * 100)
                : 0;

            return (
              <div
                key={wf.id}
                className="workflow-card"
                onClick={() => onSelectWorkflow(wf.id)}
              >
                <div className="workflow-card-main">
                  <div className="wf-top-row">
                    <span className="wf-date">{formatDate(wf.created_at)}</span>
                    {getStatusBadge(wf.status)}
                  </div>

                  <h3 className="wf-title">{wf.title}</h3>
                  <p className="wf-obj">{wf.objective}</p>

                  {/* Progress bar */}
                  <div className="wf-progress-container">
                    <div className="wf-progress-bar">
                      <div
                        className="wf-progress-fill"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <span className="wf-progress-text">
                      {wf.completed_tasks_count} of {wf.tasks_count} tasks completed ({progress}%)
                    </span>
                  </div>
                </div>

                <div className="workflow-card-stats">
                  <div className="stat-unit">
                    <span className="stat-label">Duration</span>
                    <span className="stat-number">{wf.execution_time_seconds}s</span>
                  </div>
                  <div className="stat-unit">
                    <span className="stat-label">Tokens</span>
                    <span className="stat-number">{wf.total_tokens.toLocaleString()}</span>
                  </div>
                  <button type="button" className="btn-open-wf">
                    Inspect ➔
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
