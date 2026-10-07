"""Tests for workflow API endpoints, execution engine, and approvals."""

import pytest
from fastapi.testclient import TestClient


def test_list_agents(client: TestClient) -> None:
    res = client.get("/api/v1/agents")
    assert res.status_code == 200
    agents = res.json()
    assert len(agents) >= 5
    roles = [a["role"] for a in agents]
    assert "planner" in roles
    assert "researcher" in roles
    assert "data_analyst" in roles
    assert "writer" in roles
    assert "validator" in roles


def test_list_tools(client: TestClient) -> None:
    res = client.get("/api/v1/tools")
    assert res.status_code == 200
    tools = res.json()
    assert len(tools) >= 5
    names = [t["name"] for t in tools]
    assert "web_search" in names
    assert "csv_analysis" in names
    assert "safe_python" in names
    assert "external_action" in names


def test_list_templates(client: TestClient) -> None:
    res = client.get("/api/v1/templates")
    assert res.status_code == 200
    templates = res.json()
    assert len(templates) >= 4
    ids = [t["id"] for t in templates]
    assert "market_research" in ids
    assert "financial_kpi" in ids


def test_workflow_lifecycle(client: TestClient) -> None:
    # 1. Create a workflow without auto-start so we inspect initial planned state
    create_payload = {
        "title": "Evaluate Machine Learning Models",
        "objective": "Compare latency, cost, and throughput across transformer models.",
        "require_external_approval": True,
        "auto_start": False,
    }
    create_res = client.post("/api/v1/workflows/", json=create_payload)
    assert create_res.status_code == 201
    wf = create_res.json()
    workflow_id = wf["id"]
    assert wf["title"] == "Evaluate Machine Learning Models"
    assert len(wf["tasks"]) >= 4

    # 2. Get workflow detail
    detail_res = client.get(f"/api/v1/workflows/{workflow_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == workflow_id

    # 3. List workflows
    list_res = client.get("/api/v1/workflows/")
    assert list_res.status_code == 200
    wf_list = list_res.json()
    assert any(w["id"] == workflow_id for w in wf_list)

    # 4. Pause workflow
    pause_res = client.post(f"/api/v1/workflows/{workflow_id}/pause")
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # 5. Cancel workflow
    cancel_res = client.post(f"/api/v1/workflows/{workflow_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"


@pytest.mark.anyio
async def test_full_workflow_execution_and_artifacts() -> None:
    from app.db.session import SessionLocal
    from app.models.workflow import WorkflowModel
    from app.workflows.engine import get_workflow_engine

    engine = get_workflow_engine()
    # Create workflow without external approval requirement so it runs straight to completion
    wf_id = await engine.create_and_plan(
        objective="Analyze cloud infrastructure costs and generate executive optimization report",
        require_external_approval=False,
        auto_start=False,
    )
    assert wf_id is not None

    # Run execution loop to completion
    await engine.run_execution_loop(wf_id)

    with SessionLocal() as db:
        wf = db.get(WorkflowModel, wf_id)
        assert wf is not None
        assert wf.status == "completed"
        assert len(wf.tasks) >= 4
        assert all(t.status == "completed" for t in wf.tasks)
        assert wf.total_tokens > 0
        assert wf.execution_time_seconds > 0
        assert len(wf.artifacts) >= 1
        assert "Report" in wf.artifacts[0].name


@pytest.mark.anyio
async def test_human_in_the_loop_approval_flow() -> None:
    from app.db.session import SessionLocal
    from app.models.workflow import WorkflowModel
    from app.workflows.engine import get_workflow_engine

    engine = get_workflow_engine()
    # Create workflow WITH external approval required
    wf_id = await engine.create_and_plan(
        objective="Deploy updated model weights to production cluster",
        require_external_approval=True,
        auto_start=False,
    )

    # Run execution loop until it pauses for approval
    await engine.run_execution_loop(wf_id)

    with SessionLocal() as db:
        wf = db.get(WorkflowModel, wf_id)
        assert wf is not None
        assert wf.status == "waiting_for_approval"
        waiting_task = next(t for t in wf.tasks if t.status == "waiting_for_approval")
        waiting_task_id = waiting_task.id

    # Human approves the task
    await engine.approve_task(
        wf_id, waiting_task_id, approved=True, reason="Verified by Security Lead"
    )

    # Resume execution loop to finish
    await engine.run_execution_loop(wf_id)

    with SessionLocal() as db:
        wf = db.get(WorkflowModel, wf_id)
        assert wf is not None
        assert wf.status == "completed"
