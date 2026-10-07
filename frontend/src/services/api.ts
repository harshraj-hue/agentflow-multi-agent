import type { HealthResponse, ReadinessResponse } from "../types/health";
import type {
  AgentInfo,
  ExecutionEvent,
  ToolInfo,
  Workflow,
  WorkflowSummary,
  WorkflowTemplate,
} from "../types/workflow";

// Empty by default: requests go to the same origin (Vite proxies /api in dev).
const BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function requestJson<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      let errorMsg = `Request failed (HTTP ${res.status})`;
      let details: unknown = null;
      try {
        const errorJson = await res.json();
        if (errorJson?.error?.message) {
          errorMsg = errorJson.error.message;
        } else if (errorJson?.detail) {
          errorMsg = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
        details = errorJson;
      } catch {
        // ignore parsing error
      }
      throw new ApiError(errorMsg, res.status, details);
    }

    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(`Network or connection error connecting to ${path}`);
  }
}

// System Health
export async function getHealth(): Promise<HealthResponse> {
  return requestJson<HealthResponse>("/api/v1/health");
}

export async function getReadiness(): Promise<ReadinessResponse> {
  try {
    return await requestJson<ReadinessResponse>("/api/v1/ready");
  } catch (err: unknown) {
    if (err instanceof ApiError && err.status === 503 && err.details) {
      return err.details as ReadinessResponse;
    }
    throw err;
  }
}

// Workflows
export async function listWorkflows(statusFilter?: string): Promise<WorkflowSummary[]> {
  const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
  return requestJson<WorkflowSummary[]>(`/api/v1/workflows/${query}`);
}

export async function getWorkflow(id: string): Promise<Workflow> {
  return requestJson<Workflow>(`/api/v1/workflows/${id}`);
}

export interface CreateWorkflowParams {
  objective: string;
  title?: string;
  template_id?: string;
  parameters?: Record<string, unknown>;
  require_external_approval?: boolean;
  auto_start?: boolean;
}

export async function createWorkflow(params: CreateWorkflowParams): Promise<Workflow> {
  return requestJson<Workflow>("/api/v1/workflows/", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function startWorkflow(id: string): Promise<{ status: string }> {
  return requestJson<{ status: string }>(`/api/v1/workflows/${id}/start`, { method: "POST" });
}

export async function pauseWorkflow(id: string): Promise<{ status: string }> {
  return requestJson<{ status: string }>(`/api/v1/workflows/${id}/pause`, { method: "POST" });
}

export async function cancelWorkflow(id: string): Promise<{ status: string }> {
  return requestJson<{ status: string }>(`/api/v1/workflows/${id}/cancel`, { method: "POST" });
}

export async function approveTask(
  workflowId: string,
  taskId: string,
  approved: boolean,
  reason?: string,
): Promise<{ status: string }> {
  return requestJson<{ status: string }>(
    `/api/v1/workflows/${workflowId}/tasks/${taskId}/approve`,
    {
      method: "POST",
      body: JSON.stringify({ approved, reason }),
    },
  );
}

// Catalogs
export async function listTemplates(): Promise<WorkflowTemplate[]> {
  return requestJson<WorkflowTemplate[]>("/api/v1/templates/");
}

export async function listAgents(): Promise<AgentInfo[]> {
  return requestJson<AgentInfo[]>("/api/v1/agents/");
}

export async function listTools(): Promise<ToolInfo[]> {
  return requestJson<ToolInfo[]>("/api/v1/tools/");
}

// Real-Time SSE Event Stream
export function subscribeWorkflowEvents(
  workflowId: string,
  onEvent: (event: ExecutionEvent) => void,
  onError?: (err: Event) => void,
): () => void {
  const url = `${BASE_URL}/api/v1/workflows/${workflowId}/events`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data) as ExecutionEvent;
      onEvent(data);
    } catch {
      // Ignored heartbeat or ping
    }
  };

  eventSource.onerror = (err) => {
    if (onError) onError(err);
  };

  return () => {
    eventSource.close();
  };
}
