import inspect
import logging
import re
from contextlib import AsyncExitStack
from typing import Any, List, Optional, Callable

from mcp import StdioServerParameters, ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.types import ListToolsResult, Tool

from superagentx.handler.base import BaseHandler
from superagentx.handler.decorators import tool
from superagentx.utils.helper import sync_to_async

logger = logging.getLogger(__name__)

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

    def __init__(
            self,
            command: str | None = None,
            mcp_args: list[str] | None = None,
            sse_url: str | None = None,
            headers: dict[str, str] | None = None,
            env: dict[str, str] | None = None
    ):
        """
        Initializes the MCPHandler instance with the specified command and configuration.

        :param command: The command used to launch the MCP-compatible server.
        :param mcp_args: Optional list of additional CLI arguments to pass to the server.
        :param sse_url: Optional Server-Sent Events (SSE) URL for streaming.
        :param headers: Optional HTTP headers to include in the request.
        :param env: Optional environment variables to set when running the server.
        """
        super().__init__()

        # Command and arguments for starting the MCP server
        self.command: str | None = command
        self.mcp_args: list[str] = mcp_args if mcp_args is not None else []

        # Optional runtime parameters
        self.sse_url: str | None = sse_url
        self.headers: dict[str, str] | None = headers
        self.env: dict[str, str] | None = env

        self.sse_transport = False

        # Asynchronous session for HTTP communications
        self.session: ClientSession | None = None

        # Context manager for managing multiple async resources (e.g. subprocesses, sessions)
        self.exit_stack: AsyncExitStack = AsyncExitStack()

        # I/O stream placeholders (to be initialized during process startup)
        self.write = None
        self.stdio = None

        # Internal context for managing streams (used later for tracking I/O)
        self._streams_context = None

    async def connect_to_mcp_server(self) -> ClientSession:
        """
        Establishes a connection to the MCP server using stdio transport.
        Sets up the communication channel, initializes the client session,
        and performs the handshake.

        :return: An initialized ClientSession object for interacting with the MCP server.
        """
        logger.debug(f"Connecting to Stdio MCP server with command {self.command} args: {self.mcp_args}")

        # Prepare server launch parameters with command and arguments
        server_params = StdioServerParameters(
            command=self.command,
            args=self.mcp_args,
            env=self.env

        )

        # Establish stdio transport and register it with the exit stack
        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        # Unpack the stdio reader and writer
        self.stdio, self.write = stdio_transport

        # Create and initialize the client session over stdio
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()

        return self.session

    async def connect_to_mcp_sse_server(self) -> ClientSession:
        """
        Connects to the SSE-based MCP server and initializes the session.

        :return: An initialized ClientSession object for interacting with the server.
        """
        logger.debug(f"Connecting to SSE MCP server at {self.sse_url}")

        # Establish the SSE stream context and register it with the async exit stack
        self._streams_context = await sync_to_async(sse_client, url=self.sse_url, headers=self.headers)

        # Enter the async stream context to retrieve stream components
        streams = await self.exit_stack.enter_async_context(self._streams_context)

        # Use the returned streams to create the MCP client session
        self.session = await self.exit_stack.enter_async_context(ClientSession(*streams))

        # Initialize the session (e.g., handshake, setup)
        await self.session.initialize()

        return self.session

    @tool
    async def get_mcp_tools(self) -> list[Callable]:
        """
        Fetches available tools from MCP server and converts them into Python callables.
        Chooses between SSE and stdio transport based on configuration.

        :return: A list of callable functions based on MCP tool definitions.
        """
        logger.debug(f"SSE MCP server at {self.sse_url}")
        if self.sse_url:
            # Validate SSE URL using a simple HTTP/HTTPS regex
            if not re.match(r"^https?://", self.sse_url):
                raise ValueError(f"Invalid SSE URL: {self.sse_url}")
            self.sse_transport = True  # Set True for SSE Transport, if valid SSE URL
            await self.connect_to_mcp_sse_server()
        elif self.command:
            await self.connect_to_mcp_server()
        else:
            raise ValueError(f"Invalid MCP Command or SSE URL. Either of one should be used!!!")

        tools_response: ListToolsResult = await self.session.list_tools()
        generated_funcs = [
            await create_function_from_tool(mcp_tool) for mcp_tool in tools_response.tools
        ]

        await self.cleanup()
        return generated_funcs

    async def cleanup(self):
        """
        Clean up resources and close sessions.
        """
        await self.exit_stack.aclose()
        logger.debug(f"Session Cleanup Completed!!!")
