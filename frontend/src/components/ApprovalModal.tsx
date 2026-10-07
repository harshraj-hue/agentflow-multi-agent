import React, { useState } from "react";
import type { Task } from "../types/workflow";

interface ApprovalModalProps {
  task: Task;
  onApprove: (approved: boolean, reason?: string) => Promise<void>;
  isSubmitting: boolean;
}

export const ApprovalModal: React.FC<ApprovalModalProps> = ({
  task,
  onApprove,
  isSubmitting,
}) => {
  const [reason, setReason] = useState<string>("Approved by Human Operator");

  return (
    <div className="approval-banner">
      <div className="approval-glow-border" />
      <div className="approval-content">
        <div className="approval-badge-row">
          <span className="approval-beacon-dot" />
          <span className="approval-badge-text">HUMAN-IN-THE-LOOP CHECKPOINT REQUIRED</span>
        </div>

        <div className="approval-main">
          <div className="approval-info">
            <h3 className="approval-title">Action Authorization Required</h3>
            <p className="approval-description">
              The autonomous agent squad has reached a high-impact boundary: <strong>"{task.title}"</strong>.
              Execution is paused until an authorized human reviews the proposed parameters and grants permission.
            </p>

            <div className="approval-meta-grid">
              <div className="meta-item">
                <span className="meta-label">Assigned Agent</span>
                <span className="meta-value">🛡️ {task.agent_role.toUpperCase()}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Target Tool</span>
                <span className="meta-value">🛠️ {task.assigned_tool || "external_action"}</span>
              </div>
              <div className="meta-item">
                <span className="meta-label">Task Identifier</span>
                <span className="meta-value"><code>{task.id}</code></span>
              </div>
            </div>

            <div className="approval-input-box">
              <label htmlFor="approval-feedback" className="approval-input-label">
                Operator Rationale / Instructions:
              </label>
              <input
                id="approval-feedback"
                type="text"
                className="approval-text-input"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Enter approval comments..."
              />
            </div>
          </div>

          <div className="approval-actions">
            <button
              type="button"
              className="btn-approve"
              disabled={isSubmitting}
              onClick={() => onApprove(true, reason)}
            >
              {isSubmitting ? (
                <>
                  <span className="spinner" />
                  <span>Recording...</span>
                </>
              ) : (
                <>
                  <span>✅</span>
                  <span>Authorize & Continue</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="btn-reject"
              disabled={isSubmitting}
              onClick={() => onApprove(false, reason || "Rejected by operator")}
            >
              <span>✕</span>
              <span>Reject & Abort Task</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
