"""Agents directory API endpoint."""

from fastapi import APIRouter

from app.schemas.workflow import AgentInfoResponse

router = APIRouter(prefix="/agents", tags=["agents"])

AGENTS_METADATA = [
    AgentInfoResponse(
        role="planner",
        name="Orchestrator Planner",
        description="Decomposes complex, high-level objectives into an acyclic Directed Acyclic Graph (DAG) with dependency graphs.",
        allowed_tools=[],
        system_prompt_preview="Analyzes objectives, constructs task dependencies, assigns roles and approval flags.",
    ),
    AgentInfoResponse(
        role="researcher",
        name="Research Intelligence Agent",
        description="Explores external domains, extracts facts, checks multiple sources, and complies verified evidence dossiers.",
        allowed_tools=["web_search", "web_fetch"],
        system_prompt_preview="Conducts factual searches, extracts relevant snippets, adheres to SSRF safety limits.",
    ),
    AgentInfoResponse(
        role="data_analyst",
        name="Data Analytics Agent",
        description="Computes statistical distributions, runs safe numerical operations, and extracts insights from datasets.",
        allowed_tools=["csv_analysis", "safe_python", "file_reader"],
        system_prompt_preview="Executes statistical analysis, computes descriptive metrics, and detects distribution trends.",
    ),
    AgentInfoResponse(
        role="writer",
        name="Strategic Writer Agent",
        description="Synthesizes cross-agent observations into polished, executive-ready Markdown reports with recommendations.",
        allowed_tools=["file_reader"],
        system_prompt_preview="Synthesizes findings, formats deliverables in clean Markdown with executive takeaways.",
    ),
    AgentInfoResponse(
        role="validator",
        name="Quality & Safety Validator",
        description="Performs schema validation, factual citation audits, and executes sensitive external actions post-human approval.",
        allowed_tools=["safe_python", "external_action"],
        system_prompt_preview="Audits deliverables for accuracy, scores quality, manages external action gates.",
    ),
]


@router.get("/", response_model=list[AgentInfoResponse], summary="List all specialized agents")
def list_agents() -> list[AgentInfoResponse]:
    """Return all available specialized agents and their operational capabilities."""
    return AGENTS_METADATA
