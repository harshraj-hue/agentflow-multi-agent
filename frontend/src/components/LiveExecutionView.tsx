import { useState } from "react";
import type { ExecutionEvent, Workflow } from "../types/workflow";

import { ApprovalModal } from "./ApprovalModal";
import { DeliverableReport } from "./DeliverableReport";
import { ExecutionConsole } from "./ExecutionConsole";
import { TaskGraph } from "./TaskGraph";
import { TaskInspector } from "./TaskInspector";

interface LiveExecutionViewProps {
  workflow: Workflow | null;
  events: ExecutionEvent[];
  onStart: (id: string) => Promise<void>;
  onPause: (id: string) => Promise<void>;
  onCancel: (id: string) => Promise<void>;
  onApprove: (workflowId: string, taskId: string, approved: boolean, reason?: string) => Promise<void>;
  onClearEvents: () => void;
  isLoading: boolean;
}

export const LiveExecutionView: React.FC<LiveExecutionViewProps> = ({
  workflow,
  events,
  onStart,
  onPause,
  onCancel,
  onApprove,
  onClearEvents,
  isLoading,
}) => {
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState<"graph" | "telemetry" | "deliverables">("graph");
  const [isApproving, setIsApproving] = useState<boolean>(false);

  if (!workflow) {
    return (
      <div className="no-workflow-placeholder">
        <div className="placeholder-icon">🚀</div>
        <h3>No Active Mission Selected</h3>
        <p>Launch a new mission in Mission Studio or pick a prior workflow from the library to view live telemetry.</p>
      </div>
    );
  }

  const waitingTask = workflow.tasks.find((t) => t.status === "waiting_for_approval");
  const selectedTask = workflow.tasks.find((t) => t.id === selectedTaskId) || null;

  const handleApproveAction = async (approved: boolean, reason?: string) => {
    if (!waitingTask) return;
    setIsApproving(true);
    try {
      await onApprove(workflow.id, waitingTask.id, approved, reason);
    } finally {
      setIsApproving(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return <span className="status-badge badge-running"><span className="pulse-dot" />Autonomous Run Active</span>;
      case "waiting_for_approval":
        return <span className="status-badge badge-approval"><span className="pulse-dot-amber" />Awaiting Human Sign-off</span>;
      case "completed":
        return <span className="status-badge badge-completed">✓ Mission Accomplished</span>;
      case "failed":
        return <span className="status-badge badge-failed">✕ Execution Failed</span>;
      case "paused":
        return <span className="status-badge badge-ready">⏸ Mission Paused</span>;
      case "planning":
        return <span className="status-badge badge-ready"><span className="pulse-dot" />Planning Topology</span>;
      default:
        return <span className="status-badge badge-pending">{status.toUpperCase()}</span>;
    }
  };

  const completedCount = workflow.tasks.filter((t) => t.status === "completed").length;
  const progressPercent = workflow.tasks.length > 0 ? Math.round((completedCount / workflow.tasks.length) * 100) : 0;

  return (
    <div className="live-exec-container">
      {/* Top Mission Control Bar */}
      <div className="mission-control-bar">
        <div className="mission-info-group">
          <div className="mission-title-row">
            <h2 className="mission-title">{workflow.title}</h2>
            {getStatusBadge(workflow.status)}
          </div>
          <p className="mission-objective">{workflow.objective}</p>
        </div>

        {/* Telemetry Stats & Action Controls */}
        <div className="mission-telemetry-group">
          <div className="live-stat-card">
            <span className="stat-label">Progress</span>
            <span className="stat-value">{completedCount}/{workflow.tasks.length} Tasks ({progressPercent}%)</span>
            <div className="mini-progress-bar">
              <div className="mini-progress-fill" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>

          <div className="live-stat-card">
            <span className="stat-label">Tokens</span>
            <span className="stat-value">{workflow.total_tokens.toLocaleString()}</span>
          </div>

          <div className="live-stat-card">
            <span className="stat-label">Duration</span>
            <span className="stat-value">{workflow.execution_time_seconds}s</span>
          </div>

          {/* Controls */}
          <div className="control-btn-group">
            {workflow.status === "paused" && (
              <button
                type="button"
                className="btn-control btn-resume"
                onClick={() => onStart(workflow.id)}
                disabled={isLoading}
              >
                ▶ Resume
              </button>
            )}

            {workflow.status === "running" && (
              <button
                type="button"
                className="btn-control btn-pause"
                onClick={() => onPause(workflow.id)}
                disabled={isLoading}
              >
                ⏸ Pause
              </button>
            )}

            {workflow.status !== "completed" && workflow.status !== "cancelled" && (
              <button
                type="button"
                className="btn-control btn-cancel"
                onClick={() => onCancel(workflow.id)}
                disabled={isLoading}
              >
                ✕ Cancel
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Human-in-the-Loop Banner if waiting */}
      {waitingTask && (
        <ApprovalModal
          task={waitingTask}
          onApprove={handleApproveAction}
          isSubmitting={isApproving}
        />
      )}

      {/* Sub-navigation views */}
      <div className="view-mode-bar">
        <div className="mode-tabs">
          <button
            type="button"
            className={`mode-tab ${viewTab === "graph" ? "active" : ""}`}
            onClick={() => setViewTab("graph")}
          >
            <span>🧭</span>
            <span>Task Graph & Topology</span>
          </button>
          <button
            type="button"
            className={`mode-tab ${viewTab === "telemetry" ? "active" : ""}`}
            onClick={() => setViewTab("telemetry")}
          >
            <span>📟</span>
            <span>Live Stream Telemetry</span>
            <span className="live-pulse-badge">LIVE</span>
          </button>
          <button
            type="button"
            className={`mode-tab ${viewTab === "deliverables" ? "active" : ""}`}
            onClick={() => setViewTab("deliverables")}
          >
            <span>📑</span>
            <span>Artifacts & Deliverables</span>
            {workflow.artifacts.length > 0 && (
              <span className="count-pill">{workflow.artifacts.length}</span>
            )}
          </button>
        </div>
      </div>

      {/* View Content */}
      <div className="view-content-area">
        {viewTab === "graph" && (
          <div className="graph-view-split">
            <div className="graph-main">
              <TaskGraph
                tasks={workflow.tasks}
                selectedTaskId={selectedTaskId}
                onSelectTask={(id) => setSelectedTaskId(id)}
              />
            </div>
            {selectedTask && (
              <div className="inspector-sidebar">
                <TaskInspector
                  task={selectedTask}
                  onClose={() => setSelectedTaskId(null)}
                />
              </div>
            )}
          </div>
        )}

        {viewTab === "telemetry" && (
          <ExecutionConsole
            events={events}
            onClear={onClearEvents}
          />
        )}

        {viewTab === "deliverables" && (
          <DeliverableReport
            artifacts={workflow.artifacts}
            summary={workflow.summary}
          />
        )}
      </div>
    </div>
  );
};
