import React from "react";
import type { Task } from "../types/workflow";

interface TaskGraphProps {
  tasks: Task[];
  selectedTaskId: string | null;
  onSelectTask: (taskId: string) => void;
}

export const TaskGraph: React.FC<TaskGraphProps> = ({
  tasks,
  selectedTaskId,
  onSelectTask,
}) => {
  const getRoleIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case "planner":
        return "🧠";
      case "researcher":
        return "🔍";
      case "data_analyst":
        return "📈";
      case "writer":
        return "✍️";
      case "validator":
        return "🛡️";
      default:
        return "🤖";
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "running":
        return <span className="status-badge badge-running"><span className="pulse-dot" />Running</span>;
      case "waiting_for_approval":
        return <span className="status-badge badge-approval"><span className="pulse-dot-amber" />Needs Approval</span>;
      case "completed":
        return <span className="status-badge badge-completed">✓ Completed</span>;
      case "failed":
        return <span className="status-badge badge-failed">✕ Failed</span>;
      case "ready":
        return <span className="status-badge badge-ready">Ready</span>;
      default:
        return <span className="status-badge badge-pending">Pending</span>;
    }
  };

  return (
    <div className="task-graph-container">
      <div className="graph-header">
        <div className="graph-title-row">
          <h3 className="graph-title">Directed Acyclic Task Graph (DAG)</h3>
          <span className="task-count-tag">{tasks.length} Executable Nodes</span>
        </div>
        <p className="graph-subtitle">
          Interactive workflow topology. Tasks automatically resolve dependencies and trigger assigned agents.
        </p>
      </div>

      <div className="dag-flow">
        {tasks.map((task, idx) => {
          const isSelected = selectedTaskId === task.id;
          const hasDeps = task.dependencies && task.dependencies.length > 0;

          return (
            <React.Fragment key={task.id}>
              {/* Connector line between steps */}
              {idx > 0 && (
                <div className="dag-connector">
                  <div className={`connector-line ${task.status === "completed" || task.status === "running" ? "active" : ""}`} />
                  <span className="connector-arrow">▼</span>
                </div>
              )}

              {/* Task Node */}
              <div
                className={`task-node ${task.status} ${isSelected ? "selected" : ""}`}
                onClick={() => onSelectTask(task.id)}
              >
                <div className="task-node-header">
                  <div className="node-role-pill">
                    <span className="role-icon">{getRoleIcon(task.agent_role)}</span>
                    <span className="role-name">{task.agent_role.replace("_", " ").toUpperCase()}</span>
                  </div>
                  {getStatusBadge(task.status)}
                </div>

                <h4 className="node-title">{task.title}</h4>
                <p className="node-desc">{task.description}</p>

                <div className="node-footer">
                  <div className="node-meta">
                    {task.assigned_tool && (
                      <span className="tool-pill">
                        🛠️ {task.assigned_tool}
                      </span>
                    )}
                    {task.requires_approval && (
                      <span className="approval-pill">
                        ⚠️ Guarded Action
                      </span>
                    )}
                  </div>

                  {hasDeps && (
                    <div className="deps-indicator">
                      <span>Depends on: {task.dependencies.join(", ")}</span>
                    </div>
                  )}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
