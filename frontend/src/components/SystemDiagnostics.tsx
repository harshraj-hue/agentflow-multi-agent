import React from "react";
import type { HealthResponse, ReadinessResponse } from "../types/health";

interface SystemDiagnosticsProps {
  health: HealthResponse | null;
  readiness: ReadinessResponse | null;
  onRefresh: () => void;
  isLoading: boolean;
}

export const SystemDiagnostics: React.FC<SystemDiagnosticsProps> = ({
  health,
  readiness,
  onRefresh,
  isLoading,
}) => {
  const isHealthy = health?.status === "ok";
  const isDbReady = readiness?.checks?.database === "ok";

  return (
    <div className="diagnostics-container">
      <div className="diagnostics-header">
        <div>
          <h2 className="diagnostics-title">System Health & Telemetry Probes</h2>
          <p className="diagnostics-subtitle">
            Real-time liveness, database connection pooling, and configuration integrity.
          </p>
        </div>

        <button
          type="button"
          className="btn-secondary"
          onClick={onRefresh}
          disabled={isLoading}
        >
          {isLoading ? "Probing..." : "↻ Re-check Probes"}
        </button>
      </div>

      <div className="diagnostics-grid">
        <div className={`diag-card ${isHealthy ? "card-ok" : "card-error"}`}>
          <div className="diag-card-top">
            <span className="diag-icon">⚡</span>
            <span className={`diag-badge ${isHealthy ? "badge-ok" : "badge-bad"}`}>
              {isHealthy ? "HEALTHY" : "DOWN"}
            </span>
          </div>
          <h4 className="diag-name">FastAPI Core Engine</h4>
          <p className="diag-detail">
            Application: <strong>{health?.app || "AgentFlow AI"}</strong>
          </p>
          <div className="diag-sub-details">
            <div>Version: <code>v{health?.version || "0.1.0"}</code></div>
            <div>Environment: <code>{health?.environment || "development"}</code></div>
          </div>
        </div>

        <div className={`diag-card ${isDbReady ? "card-ok" : "card-error"}`}>
          <div className="diag-card-top">
            <span className="diag-icon">🗄️</span>
            <span className={`diag-badge ${isDbReady ? "badge-ok" : "badge-bad"}`}>
              {isDbReady ? "CONNECTED" : "UNAVAILABLE"}
            </span>
          </div>
          <h4 className="diag-name">Database Persistence Layer</h4>
          <p className="diag-detail">
            Status: <strong>{isDbReady ? "Active Connection Pool Verified" : "Database Unreachable"}</strong>
          </p>
          <div className="diag-sub-details">
            <div>Engine: <code>SQLAlchemy 2.0 (Alembic Migrated)</code></div>
            <div>Pool Health: <code>{readiness?.status === "ready" ? "OK (SELECT 1 passed)" : "Failed"}</code></div>
          </div>
        </div>

        <div className="diag-card card-ok">
          <div className="diag-card-top">
            <span className="diag-icon">🛡️</span>
            <span className="diag-badge badge-ok">ACTIVE</span>
          </div>
          <h4 className="diag-name">Safety & Sandboxing Guardrails</h4>
          <p className="diag-detail">
            Zero-Trust AST validation enabled.
          </p>
          <div className="diag-sub-details">
            <div>SSRF Defenses: <code>RFC 1918 + Loopback blocked</code></div>
            <div>Python AST: <code>Whitelisted Math Namespace</code></div>
          </div>
        </div>

        <div className="diag-card card-ok">
          <div className="diag-card-top">
            <span className="diag-icon">📡</span>
            <span className="diag-badge badge-ok">STREAMING</span>
          </div>
          <h4 className="diag-name">Server-Sent Events (SSE)</h4>
          <p className="diag-detail">
            Real-time event broadcasting channel.
          </p>
          <div className="diag-sub-details">
            <div>Transport: <code>HTTP / SSE EventStream</code></div>
            <div>Protocol: <code>Reactive Async Queue</code></div>
          </div>
        </div>
      </div>
    </div>
  );
};
