import React from "react";
import type { Task } from "../types/workflow";

interface TaskInspectorProps {
  task: Task | null;
  onClose: () => void;
}

export const TaskInspector: React.FC<TaskInspectorProps> = ({ task, onClose }) => {
  if (!task) return null;

  return (
    <div className="inspector-panel">
      <div className="inspector-header">
        <div className="inspector-title-row">
          <span className="inspector-tag">TASK INSPECTOR</span>
          <button type="button" className="close-btn" onClick={onClose}>
            ✕
          </button>
        </div>
        <h3 className="inspector-task-title">{task.title}</h3>
        <p className="inspector-task-desc">{task.description}</p>
      </div>

      <div className="inspector-body">
        <div className="inspector-meta-row">
          <div className="meta-block">
            <span className="lbl">Status</span>
            <span className={`val status-${task.status}`}>{task.status.toUpperCase()}</span>
          </div>
          <div className="meta-block">
            <span className="lbl">Assigned Agent</span>
            <span className="val">🤖 {task.agent_role.toUpperCase()}</span>
          </div>
          <div className="meta-block">
            <span className="lbl">Assigned Tool</span>
            <span className="val">{task.assigned_tool ? `🛠️ ${task.assigned_tool}` : "None"}</span>
          </div>
          <div className="meta-block">
            <span className="lbl">Retries</span>
            <span className="val">{task.retry_count} / {task.max_retries}</span>
          </div>
        </div>

        {task.dependencies.length > 0 && (
          <div className="inspector-section">
            <h5 className="section-sub">Dependencies</h5>
            <div className="deps-tags">
              {task.dependencies.map((d) => (
                <span key={d} className="dep-tag">
                  ↳ {d}
                </span>
              ))}
            </div>
          </div>
        )}

        {task.error && (
          <div className="inspector-section error-section">
            <h5 className="section-sub error-sub">Execution Error</h5>
            <pre className="error-box">{task.error}</pre>
          </div>
        )}

        {task.output_data && (
          <div className="inspector-section">
            <h5 className="section-sub">Task Output & Observations</h5>
            <pre className="code-box">
              {JSON.stringify(task.output_data, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
