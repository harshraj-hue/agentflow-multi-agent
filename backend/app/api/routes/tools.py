"""Tools directory API endpoint."""

from fastapi import APIRouter

from app.schemas.workflow import ToolInfoResponse
from app.tools.registry import get_tool_registry

router = APIRouter(prefix="/tools", tags=["tools"])


@router.get("/", response_model=list[ToolInfoResponse], summary="List all registered tools")
def list_tools() -> list[ToolInfoResponse]:
    """Return all tools registered in the platform registry along with their schemas and security requirements."""
    registry = get_tool_registry()
    tools = registry.list_tools()
    return [
        ToolInfoResponse(
            name=t.name,
            description=t.description,
            category=t.category,
            requires_approval=t.requires_approval,
            parameters_schema=t.parameters_schema,
        )
        for t in tools
    ]
