import React, { useState } from "react";
import type { WorkflowTemplate } from "../types/workflow";

interface WorkflowStudioProps {
  templates: WorkflowTemplate[];
  onLaunchWorkflow: (params: {
    objective: string;
    title?: string;
    template_id?: string;
    require_external_approval: boolean;
  }) => Promise<void>;
  isLaunching: boolean;
}

export const WorkflowStudio: React.FC<WorkflowStudioProps> = ({
  templates,
  onLaunchWorkflow,
  isLaunching,
}) => {
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);
  const [objective, setObjective] = useState<string>(
    "Analyze autonomous agent execution patterns, compare failure recovery strategies, and synthesize a comprehensive strategic report with quantitative benchmarks."
  );
  const [title, setTitle] = useState<string>("");
  const [requireApproval, setRequireApproval] = useState<boolean>(true);

  const handleSelectTemplate = (tmpl: WorkflowTemplate) => {
    setSelectedTemplate(tmpl);
    setObjective(tmpl.default_objective);
    setTitle(tmpl.title);
  };

  const handleLaunch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!objective.trim()) return;

    await onLaunchWorkflow({
      objective: objective.trim(),
      title: title.trim() || undefined,
      template_id: selectedTemplate?.id,
      require_external_approval: requireApproval,
    });
  };

  return (
    <div className="studio-container">
      {/* Hero Banner */}
      <div className="studio-hero">
        <div className="hero-pill">Autonomous Multi-Agent Orchestration</div>
        <h1 className="hero-heading">
          Launch Intelligent Agent Fleets for <span className="gradient-text">Complex Objectives</span>
        </h1>
        <p className="hero-desc">
          State a high-level goal. Our autonomous agents automatically plan a Directed Acyclic Graph (DAG),
          execute tools, cross-examine observations, request human sign-off on critical actions, and return
          verified executive deliverables.
        </p>
      </div>

      {/* Preset Blueprints Carousel */}
      <div className="template-section">
        <div className="section-title-row">
          <div>
            <h3 className="section-title">Mission Blueprints</h3>
            <p className="section-subtitle">Select a pre-architected multi-agent topology or customize your own</p>
          </div>
        </div>

        <div className="template-grid">
          {templates.map((tmpl) => {
            const isSelected = selectedTemplate?.id === tmpl.id;
            return (
              <div
                key={tmpl.id}
                className={`template-card ${isSelected ? "selected" : ""}`}
                onClick={() => handleSelectTemplate(tmpl)}
              >
                <div className="template-category">{tmpl.category}</div>
                <h4 className="template-name">{tmpl.title}</h4>
                <p className="template-desc">{tmpl.description}</p>
                <div className="template-agents">
                  {tmpl.recommended_agents.map((ag) => (
                    <span key={ag} className="agent-badge">
                      {ag === "planner" && "🧠"}
                      {ag === "researcher" && "🔍"}
                      {ag === "data_analyst" && "📈"}
                      {ag === "writer" && "✍️"}
                      {ag === "validator" && "🛡️"}{" "}
                      {ag}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Mission Configuration Form */}
      <form className="studio-form" onSubmit={handleLaunch}>
        <div className="form-card">
          <div className="form-row">
            <label className="form-label" htmlFor="workflow-title">
              Mission Title (Optional)
            </label>
            <input
              id="workflow-title"
              type="text"
              className="text-input"
              placeholder="e.g. Q4 Competitor Intelligence & Benchmarks"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          <div className="form-row">
            <div className="label-with-hint">
              <label className="form-label" htmlFor="workflow-objective">
                Primary Objective & Directives *
              </label>
              <span className="hint-text">Be specific about the desired analysis, depth, and output structure</span>
            </div>
            <textarea
              id="workflow-objective"
              className="textarea-input"
              rows={4}
              required
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Describe your objective in plain English..."
            />
          </div>

          {/* Quick Suggestions Chips */}
          <div className="quick-chips">
            <span className="chip-label">Quick Prompts:</span>
            <button
              type="button"
              className="chip-btn"
              onClick={() =>
                setObjective(
                  "Conduct comprehensive market sizing and competitive analysis for AI developer tools in 2026."
                )
              }
            >
              🚀 AI Dev Tools Market
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() =>
                setObjective(
                  "Analyze operational latency metrics, error variance dispersion, and throughput bottlenecks from benchmark logs."
                )
              }
            >
              📊 System Telemetry & KPIs
            </button>
            <button
              type="button"
              className="chip-btn"
              onClick={() =>
                setObjective(
                  "Evaluate zero-trust sandboxing and SSRF defenses across cloud API services and compile compliance report."
                )
              }
            >
              🛡️ Security & SSRF Audit
            </button>
          </div>

          {/* Guardrails and Settings */}
          <div className="guardrail-panel">
            <div className="guardrail-info">
              <div className="guardrail-title">
                <span>🛡️ Human-in-the-Loop Safety Gate</span>
                <span className="badge-recommended">Recommended</span>
              </div>
              <div className="guardrail-desc">
                When enabled, tasks with external mutations or high-impact actions pause execution and request
                explicit operator authorization before proceeding.
              </div>
            </div>

            <label className="switch">
              <input
                type="checkbox"
                checked={requireApproval}
                onChange={(e) => setRequireApproval(e.target.checked)}
              />
              <span className="slider round" />
            </label>
          </div>

          {/* Active Agents Squad preview */}
          <div className="squad-preview">
            <div className="squad-title">Autonomous Agent Squad Assigned:</div>
            <div className="squad-members">
              <div className="squad-item">
                <span className="squad-icon">🧠</span>
                <div>
                  <div className="squad-name">Planner</div>
                  <div className="squad-role">DAG Topology & Task Graphs</div>
                </div>
              </div>
              <div className="squad-item">
                <span className="squad-icon">🔍</span>
                <div>
                  <div className="squad-name">Researcher</div>
                  <div className="squad-role">Web Search & Evidence Dossier</div>
                </div>
              </div>
              <div className="squad-item">
                <span className="squad-icon">📈</span>
                <div>
                  <div className="squad-name">Data Analyst</div>
                  <div className="squad-role">CSV & Statistical Modeling</div>
                </div>
              </div>
              <div className="squad-item">
                <span className="squad-icon">✍️</span>
                <div>
                  <div className="squad-name">Strategic Writer</div>
                  <div className="squad-role">Executive Synthesis & Markdown</div>
                </div>
              </div>
              <div className="squad-item">
                <span className="squad-icon">🛡️</span>
                <div>
                  <div className="squad-name">Validator</div>
                  <div className="squad-role">Quality Scoring & Gatekeeper</div>
                </div>
              </div>
            </div>
          </div>

          {/* Submit Action CTA */}
          <div className="form-submit-row">
            <button
              type="submit"
              className="launch-btn"
              disabled={isLaunching || !objective.trim()}
            >
              {isLaunching ? (
                <>
                  <span className="spinner" />
                  <span>Planning & Initializing Agents...</span>
                </>
              ) : (
                <>
                  <span>🚀</span>
                  <span>Deploy Autonomous Agents</span>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
};
