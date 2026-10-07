"""Agent base class and result contracts."""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.services.llm import BaseLLMProvider
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentStepLog:
    step_type: str  # thought | tool_call | observation | result
    content: str
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class AgentExecutionResult:
    agent_name: str
    agent_role: str
    success: bool
    output: Any
    error: str | None = None
    step_logs: list[AgentStepLog] = field(default_factory=list)
    tokens_used: int = 0
    duration_seconds: float = 0.0


class BaseAgent(ABC):
    role: str
    name: str
    description: str
    system_prompt: str
    allowed_tools: list[str]

    def __init__(self, llm: BaseLLMProvider, tool_registry: ToolRegistry) -> None:
        self.llm = llm
        self.tools = tool_registry

    @abstractmethod
    async def execute(self, task_description: str, context: dict[str, Any]) -> AgentExecutionResult:
        """Execute assigned task using reasoning, tool invocation, and observation."""
        pass
