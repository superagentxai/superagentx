"""Exercise the example through the real MCP loader and Engine execution path."""

import os
import sys
from types import SimpleNamespace

import pytest

from examples.mcp import parallel_search
from superagentx.handler.mcp import MCPHandler
from superagentx.llm.openai import OpenAIClient


class ToolSelector:
    """Deterministic tool selection; keep SuperAgentX's actual schema conversion."""

    get_tool_json = OpenAIClient.get_tool_json

    def __init__(self, fail=False):
        self.fail = fail
        self.tools = None

    async def afunc_chat_completion(self, chat_completion_params):
        self.tools = chat_completion_params.tools
        names = {tool["function"]["name"] for tool in self.tools}
        assert {"web_search", "web_fetch"} <= names
        return [SimpleNamespace(tool_calls=[
            SimpleNamespace(
                name="web_search", tool_type="function",
                arguments={
                    "objective": "Explain Python asyncio TaskGroup using official documentation",
                    "search_queries": ["site:docs.python.org asyncio TaskGroup"],
                },
            ),
            SimpleNamespace(
                name="web_fetch", tool_type="function",
                arguments={"urls": ["https://docs.python.org/3/library/asyncio-task.html"],
                           "objective": "Explain TaskGroup cancellation",
                           **({"fail": True} if self.fail else {})},
            ),
        ])]


@pytest.fixture
def local_handler(tmp_path, monkeypatch):
    server = tmp_path / "server.py"
    server.write_text('''
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("search-fixture")
@mcp.tool()
def web_search(objective: str, search_queries: list[str]) -> str:
    return "TaskGroup awaits all tasks. https://docs.python.org/3/library/asyncio-task.html"
@mcp.tool()
def web_fetch(urls: list[str], objective: str, fail: bool = False) -> str:
    if fail:
        raise ValueError("fixture fetch failed")
    return "TaskGroup cancels remaining tasks when a task fails. " + urls[0]
mcp.run(transport="stdio")
''')
    handler = MCPHandler(command=sys.executable, mcp_args=[str(server)])
    monkeypatch.setattr(parallel_search, "create_handler", lambda: handler)
    return handler


@pytest.mark.asyncio
async def test_engine_search_and_fetch(local_handler):
    selector = ToolSelector()
    text = await parallel_search.search("Explain TaskGroup", selector)
    assert len(text) == 2
    assert "awaits all tasks" in text[0]
    assert "cancels remaining tasks" in text[1]
    assert all("https://docs.python.org/" in part for part in text)
    assert selector.tools
    assert not local_handler.exit_stack._exit_callbacks


@pytest.mark.asyncio
async def test_tool_error_is_reported_and_closed(local_handler):
    with pytest.raises(RuntimeError, match="fixture fetch failed"):
        await parallel_search.search("Explain TaskGroup", ToolSelector(fail=True))
    assert not local_handler.exit_stack._exit_callbacks


@pytest.mark.asyncio
@pytest.mark.skipif(os.getenv("PARALLEL_MCP_LIVE") != "1", reason="Opt-in network check")
async def test_live_keyless_search_and_fetch(tmp_path, monkeypatch):
    # Isolate stored bridge auth and inherited search/LLM credentials.
    monkeypatch.setenv("MCP_REMOTE_CONFIG_DIR", str(tmp_path / "mcp-auth"))
    for name in list(os.environ):
        if "PARALLEL" in name or name.endswith("API_KEY"):
            monkeypatch.delenv(name)
    selector = ToolSelector()
    text = await parallel_search.search("Explain TaskGroup", selector)
    assert len(text) >= 2
    assert all("https://docs.python.org/" in part for part in text)
    assert all("TaskGroup" in part for part in text)
    for part in text:
        print(part)
