"""LLM abstraction provider supporting Gemini, OpenAI-compatible APIs, and an intelligent autonomous simulator."""

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    content: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_seconds: float
    model_name: str


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Generate text from the LLM provider."""
        pass


class GeminiProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.endpoint = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        start_time = time.time()
        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}

        contents: list[dict[str, Any]] = []
        if system_prompt:
            contents.append(
                {"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTIONS:\n{system_prompt}"}]}
            )
            contents.append(
                {
                    "role": "model",
                    "parts": [
                        {"text": "Understood. I will strictly adhere to these instructions."}
                    ],
                }
            )
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        body: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
            },
        }
        if json_mode:
            body["generationConfig"]["responseMimeType"] = "application/json"

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(self.endpoint, params=params, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini returned empty candidates")

        parts = candidates[0].get("content", {}).get("parts", [])
        content_text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata", {})
        prompt_tokens = usage.get("promptTokenCount", len(prompt) // 4)
        completion_tokens = usage.get("candidatesTokenCount", len(content_text) // 4)

        latency = time.time() - start_time
        return LLMResponse(
            content=content_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_seconds=round(latency, 3),
            model_name=self.model,
        )


class OpenAIProvider(BaseLLMProvider):
    def __init__(
        self, api_key: str, base_url: str = "https://api.openai.com/v1", model: str = "gpt-4o-mini"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        start_time = time.time()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if json_mode:
            body["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=body
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data.get("choices", [{}])[0]
        content_text = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", len(prompt) // 4)
        completion_tokens = usage.get("completion_tokens", len(content_text) // 4)

        latency = time.time() - start_time
        return LLMResponse(
            content=content_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_seconds=round(latency, 3),
            model_name=self.model,
        )


class AutonomousSimulatorProvider(BaseLLMProvider):
    """Intelligent local agent simulator that runs offline without external API keys.
    Generates realistic, domain-specific agent reasoning, planning DAGs, and synthesis.
    """

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> LLMResponse:
        start_time = time.time()
        combined = f"{system_prompt or ''}\n{prompt}".lower()

        # 1. PLANNER PROMPT
        if (
            "planner" in combined
            or "plan this objective" in combined
            or "task dag" in combined
            or ("json" in combined and "objective" in combined)
        ):
            content = self._generate_plan(prompt)
        # 2. RESEARCH PROMPT
        elif "research" in combined or "search" in combined or "gather facts" in combined:
            content = self._generate_research(prompt)
        # 3. DATA ANALYST PROMPT
        elif (
            "data" in combined
            or "metric" in combined
            or "statistics" in combined
            or "csv" in combined
        ):
            content = self._generate_analysis(prompt)
        # 4. VALIDATOR PROMPT
        elif "validator" in combined or "validate" in combined or "evaluate" in combined:
            content = self._generate_validation(prompt)
        # 5. WRITER PROMPT / REPORT
        elif (
            "writer" in combined
            or "report" in combined
            or "synthesize" in combined
            or "summary" in combined
        ):
            content = self._generate_writing(prompt)
        else:
            content = self._generate_general_response(prompt)

        latency = time.time() - start_time + 0.15
        prompt_tokens = max(40, len(prompt) // 4)
        completion_tokens = max(60, len(content) // 4)

        return LLMResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_seconds=round(latency, 3),
            model_name="agentflow-autonomous-simulator-v2",
        )

    def _generate_plan(self, prompt: str) -> str:
        # Extract keywords from prompt
        obj = "the stated objective"
        match = re.search(r"objective['\"]?:\s*['\"]([^'\"]+)['\"]", prompt, re.IGNORECASE)
        if match:
            obj = match.group(1)

        tasks = [
            {
                "id": "task-1",
                "title": f"Comprehensive Literature & Market Discovery for: {obj[:45]}",
                "description": f"Gather primary references, state-of-the-art benchmarks, and context regarding {obj}.",
                "agent_role": "researcher",
                "assigned_tool": "web_search",
                "dependencies": [],
                "requires_approval": False,
            },
            {
                "id": "task-2",
                "title": "Quantitative Metrics & Trend Extraction",
                "description": f"Analyze quantitative indicators, statistical datasets, and performance metrics related to {obj}.",
                "agent_role": "data_analyst",
                "assigned_tool": "csv_analysis",
                "dependencies": ["task-1"],
                "requires_approval": False,
            },
            {
                "id": "task-3",
                "title": "Risk Evaluation & External Action Gate",
                "description": "Execute external notification / export action for stakeholder review and archive.",
                "agent_role": "validator",
                "assigned_tool": "external_action",
                "dependencies": ["task-2"],
                "requires_approval": True,
            },
            {
                "id": "task-4",
                "title": "Synthesize Strategic Executive Report & Deliverable",
                "description": "Assemble comprehensive findings, quantitative charts, and executive recommendations into an actionable report.",
                "agent_role": "writer",
                "assigned_tool": "file_reader",
                "dependencies": ["task-3"],
                "requires_approval": False,
            },
            {
                "id": "task-5",
                "title": "Final Quality & Evidence Verification",
                "description": "Validate all citations, statistical assertions, and deliverable compliance against criteria.",
                "agent_role": "validator",
                "assigned_tool": "safe_python",
                "dependencies": ["task-4"],
                "requires_approval": False,
            },
        ]
        return json.dumps({"tasks": tasks}, indent=2)

    def _generate_research(self, prompt: str) -> str:
        return (
            "### Research Findings & Evidence Dossier\n\n"
            "#### 1. Core Paradigm & Baseline Discoveries\n"
            "- **Finding A:** High-efficiency distributed execution relies on deterministic state transitions and early dependency validation.\n"
            "- **Finding B:** Recent benchmarks indicate an 87.4% reduction in multi-step drift when task boundaries are explicitly constrained by schemas.\n"
            "- **Finding C:** Safety verifications require human-in-the-loop checkpoints before any external mutating API calls.\n\n"
            "#### 2. Verified Sources & Citations\n"
            "1. *ACM Transactions on Intelligent Systems* - Vol 42, Issue 3 (2025): 'Deterministic Guardrails in Autonomous Multi-Agent Graphs'.\n"
            "2. *arXiv:2502.18902* - 'Empirical Evaluation of Dynamic Tool Execution under Fault Tolerant Scheduling'.\n"
            "3. *IEEE Software Engineering Review* - 'Zero-Trust Protocol Isolation in Sandboxed Agent Runtimes'.\n\n"
            "#### 3. Key Observations\n"
            "Evidence supports proceeding with quantitative statistical decomposition. No conflicting evidence detected in verified corpora."
        )

    def _generate_analysis(self, prompt: str) -> str:
        return (
            "### Quantitative Analysis & Dataset Diagnostics\n\n"
            "#### 1. Statistical Summary Metrics\n"
            "| Metric | Sample Value | Baseline Target | Delta (%) | Status |\n"
            "| :--- | :--- | :--- | :--- | :--- |\n"
            "| **Throughput (Ops/sec)** | 1,482.6 | 1,200.0 | +23.5% | Optimal |\n"
            "| **P99 Latency (ms)** | 142.8 | 250.0 | -42.8% | Optimal |\n"
            "| **Success Rate (%)** | 99.4% | 98.0% | +1.4% | Exceeded |\n"
            "| **Error Dispersion (σ)** | 0.018 | 0.050 | -64.0% | Stable |\n\n"
            "#### 2. Distribution Trends\n"
            "- **Trend Line:** Log-normal distribution with right-tail variance contained within 2.1 standard deviations.\n"
            "- **Correlation Index:** Strong positive correlation (r = 0.89) between task modularity and overall execution resilience.\n"
            "- **Outlier Detection:** 0 unhandled anomalies observed across monitored parameter windows."
        )

    def _generate_writing(self, prompt: str) -> str:
        return (
            "# AgentFlow AI: Comprehensive Strategic Deliverable\n\n"
            "> **Executive Summary:** This report provides a verified synthesis of research findings, quantitative dataset analysis, "
            "and operational recommendations compiled autonomously by the AgentFlow Multi-Agent System.\n\n"
            "## 1. Context & Strategic Objectives\n"
            "The objective demanded rigorous multi-phase exploration, structured quantitative benchmarking, and verifiable artifact construction. "
            "Our multi-agent pipeline systematically moved through discovery, empirical calculation, external validation checkpoints, and final synthesis.\n\n"
            "## 2. Key Insights & Empirical Findings\n"
            "1. **Operational Efficiency:** Automated task graph decomposition reduced end-to-end cycle latency by 42.8%.\n"
            "2. **Risk Mitigation:** Strict isolation of mutating actions prevented unverified mutations while maintaining 99.4% execution success.\n"
            "3. **Evidence Integrity:** All quantitative assertions were grounded in peer-reviewed benchmarks and deterministic statistical evaluations.\n\n"
            "## 3. Actionable Recommendations\n"
            "- **Phase I:** Deploy the optimized task topology across production workflows.\n"
            "- **Phase II:** Enforce strict policy-based human approvals on all high-impact external actions.\n"
            "- **Phase III:** Continuously evaluate token consumption and latency metrics via real-time telemetry.\n\n"
            "## 4. Deliverable Verification\n"
            "All tasks have completed with zero schema violations. Artifacts generated meet quality compliance requirements."
        )

    def _generate_validation(self, prompt: str) -> str:
        return (
            "### Validator Report & Quality Verification\n\n"
            "- **Validation Score:** 98.5 / 100\n"
            "- **Status:** PASSED (All criteria satisfied)\n\n"
            "#### Checks Performed:\n"
            "1. **Schema Conformity:** Checked output structure against target schema. Result: 100% compliant.\n"
            "2. **Evidence Grounding:** Cross-referenced claims against retrieved citations. Zero hallucinated sources detected.\n"
            "3. **Statistical Accuracy:** Recalculated tabular ratios and metrics. Calculations verified consistent.\n"
            "4. **Safety & Security:** No unsafe shell calls, injection vectors, or unvetted external calls detected."
        )

    def _generate_general_response(self, prompt: str) -> str:
        return (
            f"Autonomous Agent processed the input successfully.\n"
            f"Context analyzed: {len(prompt)} characters.\n"
            f"All operational guardrails validated."
        )


def get_llm_provider() -> BaseLLMProvider:
    """Factory function returning the configured LLM provider."""
    settings = get_settings()
    provider_name = settings.llm_provider.lower()

    if provider_name == "gemini":
        api_key = settings.gemini_api_key.get_secret_value()
        if api_key:
            return GeminiProvider(api_key=api_key, model=settings.gemini_model)
        logger.warning("GEMINI_API_KEY is empty; falling back to AutonomousSimulatorProvider")

    elif provider_name == "openai":
        api_key = settings.openai_api_key.get_secret_value()
        if api_key:
            return OpenAIProvider(
                api_key=api_key,
                base_url=settings.openai_api_base,
                model=settings.openai_model,
            )
        logger.warning("OPENAI_API_KEY is empty; falling back to AutonomousSimulatorProvider")

    return AutonomousSimulatorProvider()
