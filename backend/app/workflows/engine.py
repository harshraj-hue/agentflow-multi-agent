"""Workflow engine and DAG state machine with real-time SSE event publishing and human-in-the-loop approvals."""

import asyncio
import json
import logging
import time
import uuid
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.specialized import create_agent
from app.db.session import SessionLocal
from app.models.artifact import ArtifactModel
from app.models.event import ExecutionEventModel
from app.models.task import TaskModel
from app.models.workflow import WorkflowModel
from app.services.llm import get_llm_provider
from app.tools.registry import get_tool_registry

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(UTC)


class EventBus:
    """In-memory event broadcaster for real-time SSE streaming."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue[dict[str, Any]]]] = {}

    def subscribe(self, workflow_id: str) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        if workflow_id not in self._subscribers:
            self._subscribers[workflow_id] = set()
        self._subscribers[workflow_id].add(q)
        return q

    def unsubscribe(self, workflow_id: str, q: asyncio.Queue[dict[str, Any]]) -> None:
        if workflow_id in self._subscribers:
            self._subscribers[workflow_id].discard(q)
            if not self._subscribers[workflow_id]:
                del self._subscribers[workflow_id]

    async def publish(self, workflow_id: str, event: dict[str, Any]) -> None:
        if workflow_id in self._subscribers:
            for q in list(self._subscribers[workflow_id]):
                try:
                    q.put_nowait(event)
                except Exception:
                    pass


event_bus = EventBus()


class WorkflowEngine:
    def __init__(self) -> None:
        self._running_tasks: dict[str, asyncio.Task[None]] = {}

    async def create_and_plan(
        self,
        objective: str,
        title: str | None = None,
        template_id: str | None = None,
        parameters: dict[str, Any] | None = None,
        require_external_approval: bool = True,
        auto_start: bool = True,
    ) -> str:
        """Create a new workflow, generate the initial task DAG via PlannerAgent, and optionally start execution."""
        workflow_id = str(uuid.uuid4())
        wf_title = title or f"Autonomous Run: {objective[:50]}..."

        with SessionLocal() as db:
            wf = WorkflowModel(
                id=workflow_id,
                title=wf_title,
                objective=objective,
                status="planning",
                config={
                    "template_id": template_id,
                    "parameters": parameters or {},
                    "require_external_approval": require_external_approval,
                },
                total_tokens=0,
                execution_time_seconds=0.0,
            )
            db.add(wf)
            db.commit()

        # Emit planning started event
        await self._record_event(
            workflow_id=workflow_id,
            task_id=None,
            event_type="planning_started",
            agent_name="Orchestrator Planner",
            message="Decomposing objective into task graph with Planner Agent...",
        )

        # Execute Planner Agent
        llm = get_llm_provider()
        tools = get_tool_registry()
        planner = create_agent("planner", llm, tools)
        plan_res = await planner.execute(
            task_description=objective, context={"parameters": parameters or {}}
        )

        tasks_data: list[dict[str, Any]] = plan_res.output.get("tasks", [])
        total_tokens = plan_res.tokens_used

        with SessionLocal() as db:
            workflow_obj = db.get(WorkflowModel, workflow_id)
            if not workflow_obj:
                raise RuntimeError(f"Workflow {workflow_id} not found")

            workflow_obj.total_tokens += total_tokens

            id_prefix = workflow_id[:8]
            task_id_map = {
                t.get("id", f"task-{idx+1}"): f"{id_prefix}-{t.get('id', f'task-{idx+1}')}"
                for idx, t in enumerate(tasks_data)
            }

            for idx, t in enumerate(tasks_data):
                raw_id = t.get("id", f"task-{idx+1}")
                scoped_id = task_id_map.get(raw_id, f"{id_prefix}-{raw_id}")
                scoped_deps = [task_id_map.get(dep, dep) for dep in t.get("dependencies", [])]

                # Enforce approval requirement if requested in configuration
                if not require_external_approval:
                    needs_appr = False
                else:
                    needs_appr = bool(t.get("requires_approval", False)) or (
                        t.get("assigned_tool") == "external_action"
                    )

                task_obj = TaskModel(
                    id=scoped_id,
                    workflow_id=workflow_id,
                    title=t.get("title", f"Task {idx+1}"),
                    description=t.get("description", ""),
                    agent_role=t.get("agent_role", "researcher"),
                    status="pending",
                    dependencies=scoped_deps,
                    assigned_tool=t.get("assigned_tool"),
                    requires_approval=needs_appr,
                    approval_status="none",
                    order_index=idx,
                )
                db.add(task_obj)

            workflow_obj.status = "pending"
            db.commit()


        await self._record_event(
            workflow_id=workflow_id,
            task_id=None,
            event_type="plan_completed",
            agent_name="Orchestrator Planner",
            message=f"Plan established with {len(tasks_data)} tasks. Ready for autonomous execution.",
            payload={"tasks": tasks_data},
        )

        if auto_start:
            asyncio.create_task(self.run_execution_loop(workflow_id))

        return workflow_id

    async def start(self, workflow_id: str) -> None:
        """Start or resume a workflow execution."""
        with SessionLocal() as db:
            wf = db.get(WorkflowModel, workflow_id)
            if not wf:
                raise ValueError(f"Workflow {workflow_id} not found")
            if wf.status in ("completed", "cancelled"):
                raise ValueError(
                    f"Workflow {workflow_id} is already in terminal state: {wf.status}"
                )

        asyncio.create_task(self.run_execution_loop(workflow_id))

    async def pause(self, workflow_id: str) -> None:
        """Pause a running workflow."""
        with SessionLocal() as db:
            wf = db.get(WorkflowModel, workflow_id)
            if wf and wf.status in ("running", "planning", "pending"):
                wf.status = "paused"
                db.commit()

        await self._record_event(
            workflow_id=workflow_id,
            task_id=None,
            event_type="workflow_paused",
            agent_name="System",
            message="Workflow paused by user request.",
        )

    async def cancel(self, workflow_id: str) -> None:
        """Cancel a running workflow."""
        with SessionLocal() as db:
            wf = db.get(WorkflowModel, workflow_id)
            if wf:
                wf.status = "cancelled"
                db.commit()

        await self._record_event(
            workflow_id=workflow_id,
            task_id=None,
            event_type="workflow_cancelled",
            agent_name="System",
            message="Workflow cancelled by user.",
        )

    async def approve_task(
        self, workflow_id: str, task_id: str, approved: bool, reason: str | None = None
    ) -> None:
        """Process human-in-the-loop approval or rejection for a waiting task."""
        with SessionLocal() as db:
            wf = db.get(WorkflowModel, workflow_id)
            task = db.get(TaskModel, task_id)
            if not wf or not task:
                raise ValueError(f"Workflow or task not found: {workflow_id} / {task_id}")

            if task.status != "waiting_for_approval":
                raise ValueError(
                    f"Task {task_id} is not waiting for approval (current status: {task.status})"
                )

            if approved:
                task.approval_status = "approved"
                task.approval_reason = reason or "Approved by operator"
                task.status = "ready"
                # If workflow was waiting, put it back to running
                if wf.status == "waiting_for_approval":
                    wf.status = "running"
            else:
                task.approval_status = "rejected"
                task.approval_reason = reason or "Rejected by operator"
                task.status = "failed"
                task.error = f"Rejected by human operator: {reason or 'No reason provided'}"

            db.commit()

        event_type = "task_approved" if approved else "task_rejected"
        await self._record_event(
            workflow_id=workflow_id,
            task_id=task_id,
            event_type=event_type,
            agent_name="Human Operator",
            message=f"Human operator {'approved' if approved else 'rejected'} task '{task_id}': {reason or ''}",
            payload={"approved": approved, "reason": reason},
        )

        # Trigger execution loop to continue with approved task
        if approved:
            asyncio.create_task(self.run_execution_loop(workflow_id))

    async def run_execution_loop(self, workflow_id: str) -> None:
        """Main autonomous execution loop: checks dependencies, dispatches agents, handles approvals and errors."""
        loop_start = time.time()
        logger.info("Starting execution loop for workflow %s", workflow_id)

        with SessionLocal() as db:
            wf = db.get(WorkflowModel, workflow_id)
            if not wf:
                return
            wf.status = "running"
            db.commit()

        await self._record_event(
            workflow_id=workflow_id,
            task_id=None,
            event_type="workflow_started",
            agent_name="Workflow Engine",
            message="Autonomous execution loop initialized. Evaluating DAG dependencies.",
        )

        iteration = 0
        max_iterations = 60

        while iteration < max_iterations:
            iteration += 1

            # 1. Inspect current status in DB
            with SessionLocal() as db:
                wf = db.get(WorkflowModel, workflow_id)
                if not wf or wf.status in ("paused", "cancelled"):
                    logger.info(
                        "Workflow %s stopped (status: %s)",
                        workflow_id,
                        wf.status if wf else "missing",
                    )
                    return

                tasks = db.scalars(
                    select(TaskModel)
                    .where(TaskModel.workflow_id == workflow_id)
                    .order_by(TaskModel.order_index)
                ).all()

                completed_task_ids = {t.id for t in tasks if t.status == "completed"}
                all_done = all(t.status in ("completed", "skipped") for t in tasks)
                has_failed = any(t.status == "failed" for t in tasks)

                if all_done:
                    # Finalize workflow!
                    await self._finalize_workflow_success(db, wf, tasks, loop_start)
                    return

                if has_failed:
                    wf.status = "failed"
                    wf.error = "One or more tasks failed during DAG execution."
                    db.commit()
                    await self._record_event(
                        workflow_id=workflow_id,
                        task_id=None,
                        event_type="workflow_failed",
                        agent_name="Workflow Engine",
                        message="Workflow halted due to task failure.",
                    )
                    return

                # Find tasks ready to execute
                next_task = None
                for t in tasks:
                    if t.status in ("pending", "ready"):
                        # Check dependencies
                        deps = t.dependencies or []
                        if all(dep_id in completed_task_ids for dep_id in deps):
                            next_task = t
                            break

                if not next_task:
                    # Check if any task is currently waiting for approval
                    if any(t.status == "waiting_for_approval" for t in tasks):
                        wf.status = "waiting_for_approval"
                        db.commit()
                        logger.info("Workflow %s paused waiting for human approval", workflow_id)
                        return
                    # Check if another task is running
                    if any(t.status == "running" for t in tasks):
                        await asyncio.sleep(0.5)
                        continue

                    # Deadlock or no ready tasks
                    logger.warning("No runnable tasks found for workflow %s", workflow_id)
                    return

                # Check if next_task requires approval and hasn't been approved yet
                if next_task.requires_approval and next_task.approval_status != "approved":
                    next_task.status = "waiting_for_approval"
                    wf.status = "waiting_for_approval"
                    db.commit()

                    await self._record_event(
                        workflow_id=workflow_id,
                        task_id=next_task.id,
                        event_type="approval_requested",
                        agent_name="Approval Guardrail",
                        message=f"Task '{next_task.title}' requires human approval before execution.",
                        payload={
                            "task_id": next_task.id,
                            "title": next_task.title,
                            "description": next_task.description,
                            "agent_role": next_task.agent_role,
                            "assigned_tool": next_task.assigned_tool,
                        },
                    )
                    return

                # Mark next task as running
                next_task.status = "running"
                target_task_id = next_task.id
                target_role = next_task.agent_role
                target_title = next_task.title
                target_desc = next_task.description
                db.commit()

            # 2. Execute task with assigned agent
            await self._record_event(
                workflow_id=workflow_id,
                task_id=target_task_id,
                event_type="task_started",
                agent_name=target_role.capitalize(),
                message=f"Starting task: {target_title}",
            )

            success = await self._run_single_task(
                workflow_id=workflow_id,
                task_id=target_task_id,
                agent_role=target_role,
                task_title=target_title,
                task_description=target_desc,
            )

            if not success:
                # Task execution failed and exceeded retries
                logger.error("Task %s failed completely", target_task_id)

            await asyncio.sleep(0.1)

    async def _run_single_task(
        self,
        workflow_id: str,
        task_id: str,
        agent_role: str,
        task_title: str,
        task_description: str,
    ) -> bool:
        llm = get_llm_provider()
        tools = get_tool_registry()
        agent = create_agent(agent_role, llm, tools)

        # Gather prior task outputs for context
        prior_outputs: dict[str, Any] = {}
        with SessionLocal() as db:
            tasks = db.scalars(
                select(TaskModel).where(
                    TaskModel.workflow_id == workflow_id,
                    TaskModel.status == "completed",
                )
            ).all()
            for t in tasks:
                prior_outputs[t.title] = t.output_data

        context = {"prior_outputs": prior_outputs}

        try:
            result = await agent.execute(
                task_description=f"{task_title}. {task_description}", context=context
            )

            # Stream step logs to SSE
            for step in result.step_logs:
                await self._record_event(
                    workflow_id=workflow_id,
                    task_id=task_id,
                    event_type=f"step_{step.step_type}",
                    agent_name=result.agent_name,
                    message=step.content,
                    payload=step.details or {},
                )

            # Update DB with success
            with SessionLocal() as db:
                task = db.get(TaskModel, task_id)
                wf = db.get(WorkflowModel, workflow_id)
                if task:
                    task.status = "completed"
                    task.output_data = result.output
                if wf:
                    wf.total_tokens += result.tokens_used
                db.commit()

            await self._record_event(
                workflow_id=workflow_id,
                task_id=task_id,
                event_type="task_completed",
                agent_name=result.agent_name,
                message=f"Completed task '{task_title}'.",
                payload={"tokens_used": result.tokens_used, "duration": result.duration_seconds},
            )
            return True

        except Exception as e:
            logger.exception("Error executing task %s: %s", task_id, e)
            with SessionLocal() as db:
                task = db.get(TaskModel, task_id)
                if task:
                    task.retry_count += 1
                    if task.retry_count <= task.max_retries:
                        task.status = "pending"
                        msg = f"Task failed: {str(e)}. Retrying ({task.retry_count}/{task.max_retries})..."
                    else:
                        task.status = "failed"
                        task.error = str(e)
                        msg = f"Task failed permanently: {str(e)}"
                    db.commit()

            await self._record_event(
                workflow_id=workflow_id,
                task_id=task_id,
                event_type="task_failed",
                agent_name=agent_role.capitalize(),
                message=msg,
                payload={"error": str(e)},
            )
            return False

    async def _finalize_workflow_success(
        self,
        db: Session,
        wf: WorkflowModel,
        tasks: Sequence[TaskModel],
        start_time: float,
    ) -> None:
        elapsed = round(time.time() - start_time, 2)
        wf.status = "completed"
        wf.execution_time_seconds = elapsed

        # Extract deliverables & artifacts
        report_text = ""
        analysis_data: dict[str, Any] = {}
        for t in tasks:
            if isinstance(t.output_data, dict):
                if "report_markdown" in t.output_data:
                    report_text = t.output_data["report_markdown"]
                if "statistics" in t.output_data:
                    analysis_data = t.output_data["statistics"]

        if not report_text:
            report_text = f"# Executive Report for: {wf.title}\n\nAll {len(tasks)} tasks executed successfully with validated evidence."

        wf.summary = {
            "completed_tasks": len(tasks),
            "execution_time_seconds": elapsed,
            "total_tokens": wf.total_tokens,
            "deliverable_preview": report_text[:300] + "...",
        }

        # Store Artifact: Final Markdown Report
        report_artifact = ArtifactModel(
            workflow_id=wf.id,
            name=f"{wf.title} - Final Report.md",
            artifact_type="report_markdown",
            content=report_text,
            artifact_metadata={"word_count": len(report_text.split())},
        )
        db.add(report_artifact)

        # Store Artifact: Dataset Summary JSON
        if analysis_data:
            json_artifact = ArtifactModel(
                workflow_id=wf.id,
                name="quantitative_metrics.json",
                artifact_type="structured_json",
                content=json.dumps(analysis_data, indent=2),
                artifact_metadata={"metrics_count": len(analysis_data)},
            )
            db.add(json_artifact)

        db.commit()

        await self._record_event(
            workflow_id=wf.id,
            task_id=None,
            event_type="workflow_completed",
            agent_name="Workflow Engine",
            message=f"Workflow completed successfully in {elapsed}s. Deliverables generated.",
            payload={"summary": wf.summary},
        )

    async def _record_event(
        self,
        workflow_id: str,
        task_id: str | None,
        event_type: str,
        agent_name: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """Persist event to DB and broadcast via EventBus to live SSE clients."""
        event_id = str(uuid.uuid4())
        now = _utcnow()

        event_data = {
            "id": event_id,
            "workflow_id": workflow_id,
            "task_id": task_id,
            "event_type": event_type,
            "agent_name": agent_name,
            "message": message,
            "payload": payload,
            "created_at": now.isoformat(),
        }

        # Broadcast real-time SSE event
        await event_bus.publish(workflow_id, event_data)

        # Save to database
        try:
            with SessionLocal() as db:
                event_obj = ExecutionEventModel(
                    id=event_id,
                    workflow_id=workflow_id,
                    task_id=task_id,
                    event_type=event_type,
                    agent_name=agent_name,
                    message=message,
                    payload=payload,
                    created_at=now,
                )
                db.add(event_obj)
                db.commit()
        except Exception as e:
            logger.warning("Could not persist event %s: %s", event_id, e)


# Global singleton engine instance
_engine: WorkflowEngine | None = None


def get_workflow_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine
