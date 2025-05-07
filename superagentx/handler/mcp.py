import inspect
from contextlib import AsyncExitStack
from typing import Any, List, Optional, Callable

from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import ListToolsResult, Tool

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool

# Utility: JSON schema to Python type map
JSON_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


# Infers Python type from a given JSON schema field
async def infer_type(schema: dict) -> type:
    json_type = schema.get("type", "string")
    if json_type == "array":
        return List[Any]  # Default for array types
    return JSON_TYPE_MAP.get(json_type, Any)


# Dynamically constructs a Python function based on Tool schema
async def create_function_from_tool(mcp_tool: Tool) -> Callable:
    """
    Creates a dynamic Python function signature from a tool schema.
    Used to turn tool metadata into real callable functions.
    """
    props = mcp_tool.inputSchema.get("properties")
    required = set(mcp_tool.inputSchema.get("required", []))

    parameters = []
    annotations = {}

    for name, schema in props.items():
        param_type = await infer_type(schema)
        annotations[name] = param_type

        # Build parameter with or without default
        param = inspect.Parameter(
            name=name,
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=param_type if name in required else Optional[param_type],
            default=inspect.Parameter.empty if name in required else schema.get("default", None)
        )
        parameters.append(param)

    annotations['return'] = Any
    signature = inspect.Signature(parameters)

    # Define a placeholder function and assign metadata
    def template_func(*args, **kwargs):
        pass

    template_func.__name__ = mcp_tool.name
    template_func.__doc__ = mcp_tool.description
    template_func.__annotations__ = annotations
    template_func.__signature__ = signature

    return template_func


# MCPHandler: Handles dynamic tool registration
class MCPHandler(BaseHandler):
    __type__ = "MCP"

    def __init__(self, command: str, mcp_args: list = None):
        """
        Initialize the MCPHandler with the given command and arguments.

        :param command: Command to launch the MCP-compatible server.
        :param mcp_args: Optional list of CLI arguments for the server.
        """
        super().__init__()
        self.command = command
        self.mcp_args = mcp_args or []

        self.write = None
        self.stdio = None
        self.session: ClientSession | None = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_mcp_server(self):
        """
        Establish connection to the MCP server via stdio transport.
        Initializes session and performs handshake.
        """
        server_params = StdioServerParameters(command=self.command, args=self.mcp_args)
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport

        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()
        return self.session

    @tool
    async def get_mcp_tools(self) -> list[Callable]:
        """
        Fetch and convert MCP server-exposed tools into Python functions.

        :return: List of dynamically created Python callables.
        """
        await self.connect_to_mcp_server()
        tools_response: ListToolsResult = await self.session.list_tools()

        # Convert each MCP tool definition into a callable functions
        generated_funcs = [await create_function_from_tool(mcp_tool) for mcp_tool in tools_response.tools]

        await self.cleanup()
        return generated_funcs

    async def cleanup(self):
        """
        Clean up resources and close sessions.
        """
        await self.exit_stack.aclose()
