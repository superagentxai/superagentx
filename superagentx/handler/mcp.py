import inspect
import typing
from typing import Any, Dict, List

from mcp import StdioServerParameters, ClientSession
from mcp.client.stdio import stdio_client
from mcp.types import ListToolsResult, Tool

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool


# Utility function to convert a Tool schema into a Python function dynamically
async def create_function_from_tool(mcp_tool: Tool) -> typing.Callable:
    props = mcp_tool.inputSchema["properties"]  # Extract properties from schema
    required = set(mcp_tool.inputSchema.get("required", []))  # Required fields

    parameters = []
    annotations = {}

    # Iterate over each property to construct function parameters
    for name, schema in props.items():
        param_type = await infer_type(schema)
        annotations[name] = param_type

        if name in required:
            # Required parameter
            param = inspect.Parameter(
                name=name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                annotation=param_type
            )
        else:
            # Optional parameter with default
            default = schema.get("default", None)
            param = inspect.Parameter(
                name=name,
                kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=typing.Optional[param_type]
            )
        parameters.append(param)

    # Assume function returns Any
    annotations['return'] = Any
    signature = inspect.Signature(parameters)

    # Define a placeholder function and attach metadata
    def template_func(*args, **kwargs):
        pass

    template_func.__name__ = mcp_tool.name
    template_func.__doc__ = mcp_tool.description
    template_func.__annotations__ = annotations
    template_func.__signature__ = signature

    return template_func


# Mapping from JSON schema types to Python types
JSON_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list,
    "object": dict,
}


# Infers Python type from JSON schema
async def infer_type(schema: Dict) -> type:
    json_type = schema.get("type", "string")
    if json_type == "array":
        return List[Any]  # Default to List[Any] for arrays
    return JSON_TYPE_MAP.get(json_type, Any)


# MCPHandler dynamically loads tools from an MCP-compliant stdio server
class MCPHandler(BaseHandler):
    __type__ = "MCP"

    def __init__(self, command: str, mcp_args: list = None):
        """
        Initialize the MCPHandler with the given command and arguments.

        :param command: The command to launch the MCP server process.
        :param mcp_args: Optional list of arguments for the MCP process.
        """
        super().__init__()
        self.command = command
        self.mcp_args = mcp_args if mcp_args is not None else []

    @tool
    async def get_mcp_tools(self) -> list[typing.Callable]:
        """
        Launches an MCP process via stdio and retrieves the available tools.

        :return: List of available tools from the MCP server, each as a callable function.
        """
        # Prepare parameters to start the MCP process over stdio
        server_params = StdioServerParameters(
            command=self.command,
            args=self.mcp_args,
        )

        tools: list = []

        # Open communication with the MCP server
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()  # Perform handshake/init

                # Request the list of tools supported by the server
                tools_response: ListToolsResult = await session.list_tools()

                # Append each tool to the tools list
                for mcp_tool in tools_response.tools:
                    tools.append(mcp_tool)

        # Generate Python functions from each tool schema
        generated_funcs = [await create_function_from_tool(mpc_tool) for mpc_tool in tools]
        return generated_funcs
