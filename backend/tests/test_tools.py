"""Tests for AgentFlow tools and security sandboxing."""

import pytest

from app.tools.data import CsvAnalysisTool, FileReaderTool
from app.tools.external import ExternalActionTool
from app.tools.python_exec import SafePythonTool
from app.tools.registry import get_tool_registry
from app.tools.search import WebFetchTool, WebSearchTool, is_safe_url


@pytest.mark.anyio
async def test_tool_registry() -> None:
    registry = get_tool_registry()
    assert registry.has("web_search")
    assert registry.has("web_fetch")
    assert registry.has("csv_analysis")
    assert registry.has("safe_python")
    assert registry.has("external_action")
    tools = registry.list_tools()
    assert len(tools) >= 5


@pytest.mark.anyio
async def test_web_search_tool() -> None:
    tool = WebSearchTool()
    res = await tool.execute(query="Agentic AI systems")
    assert res.success is True
    assert "results" in res.data
    assert len(res.data["results"]) > 0


@pytest.mark.anyio
async def test_ssrf_protection() -> None:
    # Localhost and private IPs must be blocked
    safe, msg = is_safe_url("http://127.0.0.1:8000/secret")
    assert safe is False
    assert "forbidden" in msg.lower() or "protected" in msg.lower()

    safe, msg = is_safe_url("http://localhost/admin")
    assert safe is False

    safe, msg = is_safe_url("http://169.254.169.254/latest/meta-data/")
    assert safe is False

    fetch_tool = WebFetchTool()
    res = await fetch_tool.execute(url="http://127.0.0.1:9000/internal")
    assert res.success is False
    assert res.error is not None
    assert "SSRF" in res.error


@pytest.mark.anyio
async def test_file_reader_tool() -> None:
    tool = FileReaderTool()
    res = await tool.execute(filename="report.md")
    assert res.success is True
    assert "report.md" in res.data["filename"]
    assert "Verified Document" in res.data["content"]


@pytest.mark.anyio
async def test_csv_analysis_tool() -> None:

    tool = CsvAnalysisTool()
    csv_data = "colA,colB\n10,foo\n20,bar\n30,baz\n"
    res = await tool.execute(csv_content=csv_data)
    assert res.success is True
    assert res.data["total_rows"] == 3
    assert res.data["total_columns"] == 2
    assert "colA" in res.data["statistics"]
    assert res.data["statistics"]["colA"]["mean"] == 20.0


@pytest.mark.anyio
async def test_safe_python_tool_allowed() -> None:
    tool = SafePythonTool()
    res = await tool.execute(code="round(sum([10.5, 20.5, 30.0]) / 3, 2)")
    assert res.success is True
    assert res.data["result"] == 20.33


@pytest.mark.anyio
async def test_safe_python_tool_blocks_unsafe_code() -> None:
    tool = SafePythonTool()

    # Block import
    res1 = await tool.execute(code="import os\nos.system('dir')")
    assert res1.success is False
    assert res1.error is not None
    assert "Security violation" in res1.error

    # Block __import__
    res2 = await tool.execute(code="__import__('os').system('dir')")
    assert res2.success is False
    assert res2.error is not None
    assert "Security violation" in res2.error

    # Block exec
    res3 = await tool.execute(code="exec('print(1)')")
    assert res3.success is False
    assert res3.error is not None
    assert "Security violation" in res3.error


@pytest.mark.anyio
async def test_external_action_tool() -> None:
    tool = ExternalActionTool()
    assert tool.requires_approval is True
    res = await tool.execute(action_type="publish_report")
    assert res.success is True
    assert res.data["status"] == "executed"
