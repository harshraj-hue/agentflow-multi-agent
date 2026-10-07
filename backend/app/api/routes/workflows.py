"""Workflow API endpoints including CRUD, execution control, and real-time SSE event streaming."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.models.artifact import ArtifactModel
from app.models.event import ExecutionEventModel
from app.models.workflow import WorkflowModel
from app.schemas.workflow import (
    ApprovalRequest,
    ArtifactResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowSummaryResponse,
)
from app.workflows.engine import event_bus, get_workflow_engine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.post(
    "/",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new workflow",
)
async def create_workflow(payload: WorkflowCreate) -> WorkflowResponse:
    """Create a new multi-agent workflow, plan task DAG, and begin autonomous execution."""
    engine = get_workflow_engine()
    workflow_id = await engine.create_and_plan(
        objective=payload.objective,
        title=payload.title,
        template_id=payload.template_id,
        parameters=payload.parameters,
        require_external_approval=payload.require_external_approval,
        auto_start=payload.auto_start,
    )

    with get_db_context() as db:
        wf = db.scalars(
            select(WorkflowModel)
            .where(WorkflowModel.id == workflow_id)
            .options(
                selectinload(WorkflowModel.tasks),
                selectinload(WorkflowModel.artifacts),
            )
        ).first()
        if not wf:
            raise NotFoundError("Workflow not found after creation.")
        return WorkflowResponse.model_validate(wf)


@router.get("/", response_model=list[WorkflowSummaryResponse], summary="List workflows")
def list_workflows(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[WorkflowSummaryResponse]:
    """List workflows ordered by creation date."""
    query = (
        select(WorkflowModel)
        .options(selectinload(WorkflowModel.tasks))
        .order_by(desc(WorkflowModel.created_at))
    )
    if status_filter:
        query = query.where(WorkflowModel.status == status_filter)

    query = query.offset(offset).limit(limit)
    workflows = db.scalars(query).all()

    result: list[WorkflowSummaryResponse] = []
    for wf in workflows:
        completed = sum(1 for t in wf.tasks if t.status == "completed")
        result.append(
            WorkflowSummaryResponse(
                id=wf.id,
                title=wf.title,
                objective=wf.objective,
                status=wf.status,
                total_tokens=wf.total_tokens,
                execution_time_seconds=wf.execution_time_seconds,
                tasks_count=len(wf.tasks),
                completed_tasks_count=completed,
                created_at=wf.created_at,
                updated_at=wf.updated_at,
            )
        )
    return result


@router.get("/{workflow_id}", response_model=WorkflowResponse, summary="Get workflow details")
def get_workflow(workflow_id: str, db: Session = Depends(get_db)) -> WorkflowResponse:
    """Retrieve detailed state of a workflow, including tasks, status, and generated artifacts."""
    wf = db.scalars(
        select(WorkflowModel)
        .where(WorkflowModel.id == workflow_id)
        .options(
            selectinload(WorkflowModel.tasks),
            selectinload(WorkflowModel.artifacts),
        )
    ).first()
    if not wf:
        raise NotFoundError(f"Workflow '{workflow_id}' not found.")
    return WorkflowResponse.model_validate(wf)


@router.post(
    "/{workflow_id}/start", status_code=status.HTTP_200_OK, summary="Start or resume workflow"
)
async def start_workflow(workflow_id: str) -> dict[str, str]:
    """Start or resume execution of a pending or paused workflow."""
    engine = get_workflow_engine()
    try:
        await engine.start(workflow_id)
        return {"status": "started", "workflow_id": workflow_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post(
    "/{workflow_id}/pause", status_code=status.HTTP_200_OK, summary="Pause running workflow"
)
async def pause_workflow(workflow_id: str) -> dict[str, str]:
    """Pause an active workflow."""
    engine = get_workflow_engine()
    await engine.pause(workflow_id)
    return {"status": "paused", "workflow_id": workflow_id}


@router.post("/{workflow_id}/cancel", status_code=status.HTTP_200_OK, summary="Cancel workflow")
async def cancel_workflow(workflow_id: str) -> dict[str, str]:
    """Cancel a workflow permanently."""
    engine = get_workflow_engine()
    await engine.cancel(workflow_id)
    return {"status": "cancelled", "workflow_id": workflow_id}


@router.post(
    "/{workflow_id}/tasks/{task_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve or reject a task needing human sign-off",
)
async def approve_task(workflow_id: str, task_id: str, payload: ApprovalRequest) -> dict[str, Any]:
    """Submit a human decision (Approve / Reject) for a task awaiting human authorization."""
    engine = get_workflow_engine()
    try:
        await engine.approve_task(
            workflow_id=workflow_id,
            task_id=task_id,
            approved=payload.approved,
            reason=payload.reason or payload.feedback,
        )
        return {
            "status": "decision_recorded",
            "workflow_id": workflow_id,
            "task_id": task_id,
            "approved": payload.approved,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/{workflow_id}/events", summary="Real-time Server-Sent Events (SSE) stream")
async def stream_workflow_events(
    workflow_id: str, db: Session = Depends(get_db)
) -> StreamingResponse:
    """Server-Sent Events endpoint streaming real-time agent thoughts, tool calls, and status updates."""
    wf = db.get(WorkflowModel, workflow_id)
    if not wf:
        raise NotFoundError(f"Workflow '{workflow_id}' not found.")

    async def event_generator() -> AsyncIterator[str]:
        # Send initial backlog of persisted events
        with get_db_context() as session:
            past_events = session.scalars(
                select(ExecutionEventModel)
                .where(ExecutionEventModel.workflow_id == workflow_id)
                .order_by(ExecutionEventModel.created_at)
            ).all()
            for evt in past_events:
                payload = {
                    "id": evt.id,
                    "workflow_id": evt.workflow_id,
                    "task_id": evt.task_id,
                    "event_type": evt.event_type,
                    "agent_name": evt.agent_name,
                    "message": evt.message,
                    "payload": evt.payload,
                    "created_at": evt.created_at.isoformat(),
                }
                yield f"data: {json.dumps(payload)}\n\n"

        # Subscribe to live events queue
        queue = event_bus.subscribe(workflow_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    if event.get("event_type") in (
                        "workflow_completed",
                        "workflow_failed",
                        "workflow_cancelled",
                    ):
                        break
                except TimeoutError:
                    # Keep-alive heartbeat
                    yield ": ping\n\n"
        finally:
            event_bus.unsubscribe(workflow_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/{workflow_id}/artifacts",
    response_model=list[ArtifactResponse],
    summary="List workflow deliverables",
)
def list_artifacts(workflow_id: str, db: Session = Depends(get_db)) -> list[ArtifactResponse]:
    """Retrieve all final artifacts and deliverables produced by the workflow."""
    artifacts = db.scalars(
        select(ArtifactModel)
        .where(ArtifactModel.workflow_id == workflow_id)
        .order_by(ArtifactModel.created_at)
    ).all()
    return [ArtifactResponse.model_validate(a) for a in artifacts]


def get_db_context() -> Session:
    """Helper to obtain a standalone session."""
    from app.db.session import SessionLocal

    return SessionLocal()
