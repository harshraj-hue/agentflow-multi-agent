import React from "react";
import type { HealthResponse, ReadinessResponse } from "../types/health";

export type TabType = "studio" | "execution" | "history" | "agents" | "diagnostics";

interface NavbarProps {
  activeTab: TabType;
  setActiveTab: (tab: TabType) => void;
  health: HealthResponse | null;
  readiness: ReadinessResponse | null;
  activeWorkflowCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  health,
  readiness,
  activeWorkflowCount,
}) => {
  const isHealthy = health?.status === "ok";
  const isDbReady = readiness?.checks?.database === "ok";

  return (
    <header className="navbar">
      <div className="navbar-container">
        {/* Brand */}
        <div className="brand" onClick={() => setActiveTab("studio")}>
          <div className="logo-orb">
            <span className="logo-sparkle" />
          </div>
          <div>
            <div className="brand-title">
              AgentFlow <span className="brand-badge">AI</span>
            </div>
            <div className="brand-subtitle">Autonomous Multi-Agent Engine</div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="nav-tabs" aria-label="Main Navigation">
          <button
            type="button"
            className={`tab-btn ${activeTab === "studio" ? "active" : ""}`}
            onClick={() => setActiveTab("studio")}
          >
            <span className="tab-icon">✨</span>
            <span>Mission Studio</span>
          </button>

          <button
            type="button"
            className={`tab-btn ${activeTab === "execution" ? "active" : ""}`}
            onClick={() => setActiveTab("execution")}
          >
            <span className="tab-icon">⚡</span>
            <span>Live Mission</span>
            {activeWorkflowCount > 0 && (
              <span className="count-pill animate-pulse">{activeWorkflowCount}</span>
            )}
          </button>

          <button
            type="button"
            className={`tab-btn ${activeTab === "history" ? "active" : ""}`}
            onClick={() => setActiveTab("history")}
          >
            <span className="tab-icon">📊</span>
            <span>Workflows</span>
          </button>

          <button
            type="button"
            className={`tab-btn ${activeTab === "agents" ? "active" : ""}`}
            onClick={() => setActiveTab("agents")}
          >
            <span className="tab-icon">🤖</span>
            <span>Agent Fleet</span>
          </button>

          <button
            type="button"
            className={`tab-btn ${activeTab === "diagnostics" ? "active" : ""}`}
            onClick={() => setActiveTab("diagnostics")}
          >
            <span className="tab-icon">🩺</span>
            <span>Diagnostics</span>
          </button>
        </nav>

        {/* Health status pill */}
        <div className="health-pill" onClick={() => setActiveTab("diagnostics")}>
          <span className={`status-dot ${isHealthy && isDbReady ? "dot-online" : "dot-warning"}`} />
          <span className="health-text">
            {isHealthy && isDbReady
              ? "All Systems Online"
              : isHealthy
              ? "DB Reconnecting"
              : "API Connecting..."}
          </span>
        </div>
      </div>
    </header>
  );
};
