export type WorkflowStatus =
  | "pending"
  | "planning"
  | "running"
  | "waiting_for_approval"
  | "paused"
  | "completed"
  | "failed"
  | "cancelled";

export type TaskStatus =
  | "pending"
  | "ready"
  | "running"
  | "waiting_for_approval"
  | "completed"
  | "failed"
  | "skipped";

export interface Task {
  id: str;
  workflow_id: string;
  title: string;
  description: string;
  agent_role: "planner" | "researcher" | "data_analyst" | "writer" | "validator" | string;
  status: TaskStatus;
  dependencies: string[];
  assigned_tool?: string | null;
  input_data?: Record<string, unknown> | null;
  output_data?: Record<string, unknown> | null;
  error?: string | null;
  retry_count: number;
  max_retries: number;
  requires_approval: boolean;
  approval_status: "none" | "pending" | "approved" | "rejected";
  approval_reason?: string | null;
  order_index: number;
  created_at: string;
  updated_at: string;
}

export interface Artifact {
  id: string;
  workflow_id: string;
  task_id?: string | null;
  name: string;
  artifact_type: "report_markdown" | "dataset_csv" | "structured_json" | "chart_spec" | string;
  content: string;
  artifact_metadata?: Record<string, unknown> | null;
  created_at: string;
}

export interface Workflow {
  id: string;
  title: string;
  objective: string;
  status: WorkflowStatus;
  config: {
    template_id?: string;
    parameters?: Record<string, unknown>;
    require_external_approval?: boolean;
  };
  summary?: {
    completed_tasks?: number;
    execution_time_seconds?: number;
    total_tokens?: number;
    deliverable_preview?: string;
  } | null;
  error?: string | null;
  total_tokens: number;
  execution_time_seconds: number;
  created_at: string;
  updated_at: string;
  tasks: Task[];
  artifacts: Artifact[];
}

export interface WorkflowSummary {
  id: string;
  title: string;
  objective: string;
  status: WorkflowStatus;
  total_tokens: number;
  execution_time_seconds: number;
  tasks_count: number;
  completed_tasks_count: number;
  created_at: string;
  updated_at: string;
}

export interface ExecutionEvent {
  id: string;
  workflow_id: string;
  task_id?: string | null;
  event_type: string;
  agent_name: string;
  message: string;
  payload?: Record<string, unknown> | null;
  created_at: string;
}

export interface WorkflowTemplate {
  id: string;
  title: string;
  category: string;
  description: string;
  default_objective: string;
  recommended_agents: string[];
  parameters: Record<string, unknown>;
}

export interface AgentInfo {
  role: string;
  name: string;
  description: string;
  allowed_tools: string[];
  system_prompt_preview: string;
}

export interface ToolInfo {
  name: string;
  description: string;
  category: string;
  requires_approval: boolean;
  parameters_schema: Record<string, unknown>;
}

type str = string;
