import { useEffect, useRef, useState } from "react";

import { AgentsDirectory } from "./components/AgentsDirectory";
import { LiveExecutionView } from "./components/LiveExecutionView";
import { Navbar, type TabType } from "./components/Navbar";
import { SystemDiagnostics } from "./components/SystemDiagnostics";
import { WorkflowHistory } from "./components/WorkflowHistory";
import { WorkflowStudio } from "./components/WorkflowStudio";
import {
  approveTask,
  cancelWorkflow,
  createWorkflow,
  getHealth,
  getReadiness,
  getWorkflow,
  listAgents,
  listTemplates,
  listTools,
  listWorkflows,
  pauseWorkflow,
  startWorkflow,
  subscribeWorkflowEvents,
} from "./services/api";
import type { HealthResponse, ReadinessResponse } from "./types/health";
import type {
  AgentInfo,
  ExecutionEvent,
  ToolInfo,
  Workflow,
  WorkflowSummary,
  WorkflowTemplate,
} from "./types/workflow";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabType>("studio");

  // Health
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState<boolean>(false);

  // Catalogs
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [tools, setTools] = useState<ToolInfo[]>([]);

  // Workflows
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<Workflow | null>(null);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [isLaunching, setIsLaunching] = useState<boolean>(false);
  const [isActionLoading, setIsActionLoading] = useState<boolean>(false);

  const eventUnsubRef = useRef<(() => void) | null>(null);

  // Initial load
  useEffect(() => {
    loadHealth();
    loadCatalogs();
    loadWorkflows();
  }, []);

  // Real-time SSE subscription when activeWorkflow changes
  useEffect(() => {
    if (eventUnsubRef.current) {
      eventUnsubRef.current();
      eventUnsubRef.current = null;
    }

    if (activeWorkflow?.id) {
      const unsub = subscribeWorkflowEvents(
        activeWorkflow.id,
        (evt: ExecutionEvent) => {
          setEvents((prev) => [...prev, evt]);

          // When significant events happen, refresh workflow state
          if (
            evt.event_type.startsWith("task_") ||
            evt.event_type.startsWith("workflow_") ||
            evt.event_type === "approval_requested"
          ) {
            refreshActiveWorkflow(activeWorkflow.id);
            loadWorkflows();
          }
        },
        () => {
          // Fallback polling if SSE drops
        }
      );
      eventUnsubRef.current = unsub;
    }

    return () => {
      if (eventUnsubRef.current) {
        eventUnsubRef.current();
        eventUnsubRef.current = null;
      }
    };
  }, [activeWorkflow?.id]);

  const loadHealth = async () => {
    setIsHealthLoading(true);
    try {
      const [h, r] = await Promise.allSettled([getHealth(), getReadiness()]);
      if (h.status === "fulfilled") setHealth(h.value);
      if (r.status === "fulfilled") setReadiness(r.value);
    } finally {
      setIsHealthLoading(false);
    }
  };

  const loadCatalogs = async () => {
    try {
      const [t, a, tl] = await Promise.all([
        listTemplates(),
        listAgents(),
        listTools(),
      ]);
      setTemplates(t);
      setAgents(a);
      setTools(tl);
    } catch {
      // API may be booting
    }
  };

  const loadWorkflows = async () => {
    try {
      const wfList = await listWorkflows();
      setWorkflows(wfList);
    } catch {
      // Ignored
    }
  };

  const refreshActiveWorkflow = async (workflowId: string) => {
    try {
      const updated = await getWorkflow(workflowId);
      setActiveWorkflow(updated);
    } catch {
      // Ignored
    }
  };

  // Launch new workflow from Studio
  const handleLaunchWorkflow = async (params: {
    objective: string;
    title?: string;
    template_id?: string;
    require_external_approval: boolean;
  }) => {
    setIsLaunching(true);
    try {
      const newWf = await createWorkflow({
        ...params,
        auto_start: true,
      });
      setActiveWorkflow(newWf);
      setEvents([]);
      setActiveTab("execution");
      await loadWorkflows();
    } finally {
      setIsLaunching(false);
    }
  };

  // Select historical workflow
  const handleSelectWorkflow = async (id: string) => {
    setIsActionLoading(true);
    try {
      const wf = await getWorkflow(id);
      setActiveWorkflow(wf);
      setEvents([]);
      setActiveTab("execution");
    } finally {
      setIsActionLoading(false);
    }
  };

  // Workflow execution controls
  const handleStart = async (id: string) => {
    setIsActionLoading(true);
    try {
      await startWorkflow(id);
      await refreshActiveWorkflow(id);
      await loadWorkflows();
    } finally {
      setIsActionLoading(false);
    }
  };

  const handlePause = async (id: string) => {
    setIsActionLoading(true);
    try {
      await pauseWorkflow(id);
      await refreshActiveWorkflow(id);
      await loadWorkflows();
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleCancel = async (id: string) => {
    setIsActionLoading(true);
    try {
      await cancelWorkflow(id);
      await refreshActiveWorkflow(id);
      await loadWorkflows();
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleApprove = async (
    workflowId: string,
    taskId: string,
    approved: boolean,
    reason?: string
  ) => {
    setIsActionLoading(true);
    try {
      await approveTask(workflowId, taskId, approved, reason);
      await refreshActiveWorkflow(workflowId);
      await loadWorkflows();
    } finally {
      setIsActionLoading(false);
    }
  };

  const runningCount = workflows.filter((w) => w.status === "running" || w.status === "waiting_for_approval").length;

  return (
    <div className="app-shell">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        readiness={readiness}
        activeWorkflowCount={runningCount}
      />

      <main className="main-content">
        {activeTab === "studio" && (
          <WorkflowStudio
            templates={templates}
            onLaunchWorkflow={handleLaunchWorkflow}
            isLaunching={isLaunching}
          />
        )}

        {activeTab === "execution" && (
          <LiveExecutionView
            workflow={activeWorkflow}
            events={events}
            onStart={handleStart}
            onPause={handlePause}
            onCancel={handleCancel}
            onApprove={handleApprove}
            onClearEvents={() => setEvents([])}
            isLoading={isActionLoading}
          />
        )}

        {activeTab === "history" && (
          <WorkflowHistory
            workflows={workflows}
            onSelectWorkflow={handleSelectWorkflow}
            onRefresh={loadWorkflows}
            isLoading={isActionLoading}
          />
        )}

        {activeTab === "agents" && (
          <AgentsDirectory
            agents={agents}
            tools={tools}
          />
        )}

        {activeTab === "diagnostics" && (
          <SystemDiagnostics
            health={health}
            readiness={readiness}
            onRefresh={loadHealth}
            isLoading={isHealthLoading}
          />
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <span>AgentFlow AI • Autonomous Multi-Agent Workflows & Governance</span>
          <span>Zero-Trust Sandboxing • Human-in-the-Loop • Durable PostgreSQL</span>
        </div>
      </footer>
    </div>
  );
}
