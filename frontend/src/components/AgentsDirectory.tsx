import React from "react";
import type { AgentInfo, ToolInfo } from "../types/workflow";

interface AgentsDirectoryProps {
  agents: AgentInfo[];
  tools: ToolInfo[];
}

export const AgentsDirectory: React.FC<AgentsDirectoryProps> = ({
  agents,
  tools,
}) => {
  return (
    <div className="directory-container">
      {/* Agents Section */}
      <div className="directory-section">
        <div className="section-head-box">
          <h2 className="section-title">Specialized Autonomous Agent Squad</h2>
          <p className="section-subtitle">
            Cooperating multi-agent roles with specialized prompting, tool access constraints, and state machine loops.
          </p>
        </div>

        <div className="agents-grid">
          {agents.map((ag) => (
            <div key={ag.role} className="agent-card">
              <div className="agent-header">
                <div className="agent-avatar">
                  {ag.role === "planner" && "🧠"}
                  {ag.role === "researcher" && "🔍"}
                  {ag.role === "data_analyst" && "📈"}
                  {ag.role === "writer" && "✍️"}
                  {ag.role === "validator" && "🛡️"}
                </div>
                <div>
                  <h4 className="agent-name">{ag.name}</h4>
                  <span className="role-tag">{ag.role.toUpperCase()}</span>
                </div>
              </div>

              <p className="agent-desc">{ag.description}</p>

              <div className="agent-prompt-box">
                <span className="box-label">System Directive:</span>
                <p className="prompt-text">"{ag.system_prompt_preview}"</p>
              </div>

              <div className="agent-tools-box">
                <span className="box-label">Permitted Tools:</span>
                <div className="tool-chips">
                  {ag.allowed_tools.length === 0 ? (
                    <span className="tool-none">Pure Reasoning (No external tools)</span>
                  ) : (
                    ag.allowed_tools.map((t) => (
                      <span key={t} className="tool-chip">
                        🛠️ {t}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tools Section */}
      <div className="directory-section" style={{ marginTop: "3rem" }}>
        <div className="section-head-box">
          <h2 className="section-title">Platform Tool Registry & Sandboxes</h2>
          <p className="section-subtitle">
            Deterministic tools equipped with SSRF defenses, AST mathematical sandboxing, and policy-based human approvals.
          </p>
        </div>

        <div className="tools-grid">
          {tools.map((tl) => (
            <div key={tl.name} className="tool-card">
              <div className="tool-header">
                <div>
                  <h4 className="tool-name"><code>{tl.name}</code></h4>
                  <span className="category-tag">{tl.category}</span>
                </div>

                {tl.requires_approval ? (
                  <span className="badge-guarded">⚠️ Human Sign-off Required</span>
                ) : (
                  <span className="badge-auto">⚡ Autonomous Execution</span>
                )}
              </div>

              <p className="tool-desc">{tl.description}</p>

              <div className="tool-schema-box">
                <span className="box-label">Parameter Contract:</span>
                <pre className="schema-code">
                  {JSON.stringify(tl.parameters_schema, null, 2)}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
