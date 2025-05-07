import inspect
import logging

import pytest
from pydantic import typing

from superagentx.handler.mcp import MCPHandler

logger = logging.getLogger(__name__)

'''
 Run Pytest:  

   1. pytest --log-cli-level=INFO tests/handlers/test_mcp_handler.py::TestMCPHandler::test_get_mcp_tools

'''


@pytest.fixture
def mcp_handler_init() -> MCPHandler:
    mcp_handler = MCPHandler(command="npx",
                             mcp_args=["-y", "@modelcontextprotocol/server-memory"])

    logger.info(mcp_handler)
    return mcp_handler


class TestMCPHandler:

    @pytest.mark.asyncio
    async def test_get_mcp_tools(self, mcp_handler_init: MCPHandler):
        tools = await mcp_handler_init.get_mcp_tools()
        logger.info(f"MCP Tools {tools}")

    @pytest.mark.asyncio
    async def test_load_and_run_if_mcp(self, mcp_handler_init: MCPHandler):
        """
            Dynamically loads and runs `get_mcp_tools()` if handler has __type__ = "MCP".
            """
        if getattr(mcp_handler_init, "__type__", None) == "MCP":
            func = getattr(mcp_handler_init, "get_mcp_tools", None)
            if callable(func):
                tools = await func()
                logger.info(f"Dynamic MCP Tools Loader .. {tools}")

                if isinstance(func, typing.Callable):
                    _func_name = func.__name__
                    _doc_str = inspect.getdoc(func)
                    _properties = {}
                    _type_hints = typing.get_type_hints(func)
                    logger.info(f"Function Name - {list(_type_hints)}")
