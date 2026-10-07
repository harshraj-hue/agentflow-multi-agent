"""Workflow preset templates API endpoint."""

from fastapi import APIRouter

from app.schemas.workflow import WorkflowTemplateResponse

router = APIRouter(prefix="/templates", tags=["templates"])

TEMPLATES = [
    WorkflowTemplateResponse(
        id="market_research",
        title="Market & Competitive Intelligence",
        category="Market Analysis",
        description="Autonomous multi-agent research into market sizing, key competitors, technological moats, and industry dynamics.",
        default_objective="Analyze current trends, key market players, market growth drivers, and strategic risks in autonomous agent platforms.",
        recommended_agents=["planner", "researcher", "data_analyst", "writer", "validator"],
        parameters={"depth": "comprehensive", "focus": "competitors_and_moats"},
    ),
    WorkflowTemplateResponse(
        id="financial_kpi",
        title="Financial Health & Operational KPIs",
        category="Financial Analytics",
        description="Quantitative decomposition of revenue, unit economics, churn rate, latency distributions, and statistical anomalies.",
        default_objective="Evaluate quarterly operational KPIs, compute variance dispersion, and pinpoint throughput bottlenecks with recommendations.",
        recommended_agents=["planner", "data_analyst", "writer", "validator"],
        parameters={"dataset": "operational_metrics", "target_variance": 0.05},
    ),
    WorkflowTemplateResponse(
        id="tech_due_diligence",
        title="Technical Architecture & Security Audit",
        category="Technical Audit",
        description="In-depth evaluation of system scalability, zero-trust sandbox safety, failure recovery models, and cloud readiness.",
        default_objective="Audit system fault tolerance, evaluate SSRF defenses, verify sandboxed AST execution, and generate compliance deliverable.",
        recommended_agents=["planner", "researcher", "validator", "writer"],
        parameters={"compliance_standard": "zero_trust", "sandbox": "strict"},
    ),
    WorkflowTemplateResponse(
        id="incident_rca",
        title="Root Cause Analysis & Incident Postmortem",
        category="DevOps & Reliability",
        description="Structured investigation of incident logs, chronological timeline reconstruction, and corrective prevention actions.",
        default_objective="Investigate telemetry alerts, extract root cause factors, verify recovery effectiveness, and export stakeholder report.",
        recommended_agents=["planner", "researcher", "data_analyst", "writer", "validator"],
        parameters={"severity": "P1", "require_approval": True},
    ),
]


@router.get("/", response_model=list[WorkflowTemplateResponse], summary="List workflow templates")
def list_templates() -> list[WorkflowTemplateResponse]:
    """Retrieve pre-configured multi-agent workflow blueprints."""
    return TEMPLATES
