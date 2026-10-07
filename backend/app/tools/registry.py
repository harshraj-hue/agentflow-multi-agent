"""Central tool registry."""

import logging
from typing import Any

from app.tools.base import BaseTool, ToolResult
from app.tools.data import CsvAnalysisTool, FileReaderTool
from app.tools.external import ExternalActionTool
from app.tools.python_exec import SafePythonTool
from app.tools.search import WebFetchTool, WebSearchTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' is not registered in the registry.",
            )
        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            logger.exception("Error executing tool %s: %s", tool_name, e)
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution exception: {str(e)}",
            )

    def _register_default_tools(self) -> None:
        self.register(WebSearchTool())
        self.register(WebFetchTool())
        self.register(CsvAnalysisTool())
        self.register(FileReaderTool())
        self.register(SafePythonTool())
        self.register(ExternalActionTool())


# Global singleton instance
_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry
