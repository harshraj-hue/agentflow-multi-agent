"""Schemas for workflows, tasks, events, and artifacts."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TaskResponse(BaseModel):
    id: str
    workflow_id: str
    title: str
    description: str
    agent_role: str
    status: str
    dependencies: list[str] = Field(default_factory=list)
    assigned_tool: str | None = None
    input_data: dict[str, Any] | None = None
    output_data: dict[str, Any] | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    requires_approval: bool = False
    approval_status: str = "none"
    approval_reason: str | None = None
    order_index: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExecutionEventResponse(BaseModel):
    id: str
    workflow_id: str
    task_id: str | None = None
    event_type: str
    agent_name: str
    message: str
    payload: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ArtifactResponse(BaseModel):
    id: str
    workflow_id: str
    task_id: str | None = None
    name: str
    artifact_type: str
    content: str
    artifact_metadata: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowCreate(BaseModel):
    title: str | None = None
    objective: str = Field(
        ..., min_length=5, description="High-level goal for the multi-agent system"
    )
    template_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    require_external_approval: bool = True
    auto_start: bool = True


class WorkflowResponse(BaseModel):
    id: str
    title: str
    objective: str
    status: str
    config: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] | None = None
    error: str | None = None
    total_tokens: int = 0
    execution_time_seconds: float = 0.0
    created_at: datetime
    updated_at: datetime
    tasks: list[TaskResponse] = Field(default_factory=list)
    artifacts: list[ArtifactResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class WorkflowSummaryResponse(BaseModel):
    id: str
    title: str
    objective: str
    status: str
    total_tokens: int
    execution_time_seconds: float
    tasks_count: int
    completed_tasks_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    approved: bool
    reason: str | None = None
    feedback: str | None = None


class AgentInfoResponse(BaseModel):
    role: str
    name: str
    description: str
    allowed_tools: list[str]
    system_prompt_preview: str


class ToolInfoResponse(BaseModel):
    name: str
    description: str
    category: str
    requires_approval: bool
    parameters_schema: dict[str, Any]


class WorkflowTemplateResponse(BaseModel):
    id: str
    title: str
    category: str
    description: str
    default_objective: str
    recommended_agents: list[str]
    parameters: dict[str, Any]
