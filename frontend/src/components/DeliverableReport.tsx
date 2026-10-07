import React, { useState } from "react";
import type { Artifact } from "../types/workflow";

interface DeliverableReportProps {
  artifacts: Artifact[];
  summary?: {
    completed_tasks?: number;
    execution_time_seconds?: number;
    total_tokens?: number;
  } | null;
}

export const DeliverableReport: React.FC<DeliverableReportProps> = ({
  artifacts,
  summary,
}) => {
  const [activeArtifactId, setActiveArtifactId] = useState<string>(
    artifacts[0]?.id || ""
  );
  const [copied, setCopied] = useState<boolean>(false);

  const activeArtifact =
    artifacts.find((a) => a.id === activeArtifactId) || artifacts[0];

  const handleCopy = () => {
    if (activeArtifact?.content) {
      navigator.clipboard.writeText(activeArtifact.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!activeArtifact) return;
    const blob = new Blob([activeArtifact.content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = activeArtifact.name;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!artifacts || artifacts.length === 0) {
    return (
      <div className="empty-deliverables">
        <div className="empty-icon">📄</div>
        <h4>Deliverables in Progress</h4>
        <p>Artifacts, final executive reports, and quantitative datasets will appear here as the agent fleet finishes tasks.</p>
      </div>
    );
  }

  return (
    <div className="deliverable-container">
      {/* Top metrics summary bar */}
      {summary && (
        <div className="metrics-summary-bar">
          <div className="metric-badge">
            <span className="metric-label">Execution Time</span>
            <span className="metric-val">{summary.execution_time_seconds ?? 0}s</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Tokens Consumed</span>
            <span className="metric-val">{(summary.total_tokens ?? 0).toLocaleString()}</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Tasks Finished</span>
            <span className="metric-val">{summary.completed_tasks ?? 0}</span>
          </div>
          <div className="metric-badge">
            <span className="metric-label">Artifacts Produced</span>
            <span className="metric-val">{artifacts.length}</span>
          </div>
        </div>
      )}

      {/* Artifact switcher tabs */}
      <div className="artifact-toolbar">
        <div className="artifact-tabs">
          {artifacts.map((art) => (
            <button
              key={art.id}
              type="button"
              className={`artifact-tab-btn ${
                (activeArtifact?.id === art.id) ? "active" : ""
              }`}
              onClick={() => setActiveArtifactId(art.id)}
            >
              <span>{art.artifact_type === "report_markdown" ? "📑" : "📊"}</span>
              <span>{art.name}</span>
            </button>
          ))}
        </div>

        <div className="artifact-actions">
          <button type="button" className="btn-secondary" onClick={handleCopy}>
            {copied ? "✓ Copied!" : "📋 Copy"}
          </button>
          <button type="button" className="btn-secondary" onClick={handleDownload}>
            💾 Download
          </button>
        </div>
      </div>

      {/* Content viewer */}
      <div className="artifact-viewer">
        {activeArtifact?.artifact_type === "structured_json" ? (
          <pre className="json-viewer">
            {activeArtifact.content}
          </pre>
        ) : (
          <div className="markdown-render-box">
            {/* Simple Markdown preview rendering with clean sections */}
            <pre className="report-markdown-text">{activeArtifact?.content}</pre>
          </div>
        )}
      </div>
    </div>
  );
};
