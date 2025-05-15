import inspect
import logging
import typing

from mcp import ClientSession

from superagentx.exceptions import ToolError
from superagentx.handler.base import BaseHandler
from superagentx.handler.exceptions import InvalidHandler
from superagentx.llm import LLMClient, ChatCompletionParams
from superagentx.prompt import PromptTemplate
from superagentx.utils.helper import iter_to_aiter, sync_to_async, rm_trailing_spaces
from superagentx.utils.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class Engine:
    """
    Core execution engine to wrap a handler and invoke tool functions
    using a language model and tool metadata.
    """

    def __init__(
            self,
            *,
            handler: BaseHandler,
            llm: LLMClient,
            prompt_template: PromptTemplate,
            tools: list[dict] | list[str] | None = None,
            output_parser: BaseParser | None = None
    ):
        """
        Initializes the Engine.

        Args:
            handler: An implementation of BaseHandler with methods as callable tools.
            llm: The LLM client used to interact with the language model.
            prompt_template: Used to format the input prompt.
            tools: Optional explicit list of tool method names or tool metadata.
            output_parser: Optional parser to process and format tool outputs.
        """
        self.handler = handler
        self.llm = llm
        self.prompt_template = prompt_template
        self.tools = tools
        self.output_parser = output_parser

    def __str__(self):
        return f'Engine {self.handler.__class__}'

    async def __funcs_props(self, funcs: list[str]) -> list[dict]:
        """
        Convert tool names into LLM-compatible function schemas.

        Args:
            funcs: List of function names (str) or functions from MCP handler.

        Returns:
            List of function schema dictionaries.
        """
        _funcs_props: list[dict] = []

        if getattr(self.handler, "__type__", None) == "MCP":
            # MCP handler: dynamically fetch tool functions
            get_tools_func = getattr(self.handler, "get_mcp_tools", None)
            if inspect.isfunction(get_tools_func) or inspect.ismethod(get_tools_func):
                funcs = await get_tools_func()
                async for func in iter_to_aiter(funcs):
                    logger.debug(f"MCP Tool Function Name: {func}")
                    _funcs_props.append(await self.llm.get_tool_json(func=func))
        else:
            # Regular handler: lookup functions by name
            async for func_name in iter_to_aiter(funcs):
                logger.debug(f"Looking up handler method: {func_name}")
                func_attr = getattr(self.handler, func_name.split('.')[-1], None)
                if inspect.isfunction(func_attr) or inspect.ismethod(func_attr):
                    _funcs_props.append(await self.llm.get_tool_json(func=func_attr))
        return _funcs_props

    async def _construct_tools(self) -> list[dict]:
        """
        Construct tool metadata to send to the LLM.

        Returns:
            List of tool definitions in JSON format.
        """
        funcs = self.handler.tools or dir(self.handler)
        logger.debug(f"Resolved handler methods: {funcs}")
        if not funcs:
            raise InvalidHandler(f"No methods found in handler: {self.handler}")

        # Use explicitly provided tools if any, otherwise infer all from handler
        return await self.__funcs_props(funcs=self.tools or funcs)

    async def start(
            self,
            input_prompt: str,
            pre_result: str | None = None,
            old_memory: list[dict] | None = None,
            conversation_id: str | None = None,
            **kwargs
    ) -> list[typing.Any]:
        """
        Execute the engine pipeline using the LLM and selected handler tools.

        Args:
            input_prompt: The main input instruction to process.
            pre_result: Optional string to prepend to the prompt.
            old_memory: List of previous context (memory).
            conversation_id: Unique identifier for the conversation session.
            kwargs: Dynamic parameters for the prompt template.

        Returns:
            A list of parsed or raw results depending on output parser.
        """
        # Incorporate pre-result and conversation context into the prompt
        if pre_result:
            input_prompt += f'\n\n{pre_result}'
        input_prompt += f"\nConversation Id: {conversation_id}"

        kwargs = kwargs or {}

        # Prepare prompt messages
        messages = await self.prompt_template.get_messages(
            input_prompt=input_prompt,
            old_memory=old_memory,
            **kwargs
        )
        messages = await rm_trailing_spaces(messages)
        logger.debug(f"Final prompt messages: {messages}")

        # Get callable tool definitions
        tools = await self._construct_tools()
        logger.debug(f"Available tools: {tools}")

        # Construct chat completion parameters
        chat_params = ChatCompletionParams(messages=messages, tools=tools)
        logger.debug(f"Chat Params: {chat_params.model_dump_json(exclude_none=True)}")

        # Get tool call suggestions from the LLM
        messages = await self.llm.afunc_chat_completion(chat_completion_params=chat_params)
        if not messages:
            raise ToolError("No tools matched or executed!")

        results = []

        # Process each message returned by the LLM
        async for message in iter_to_aiter(messages):
            if message.tool_calls:
                if getattr(self.handler, "__type__", None) == "MCP":

                    # Special handling for MCP-based tools by SSE transport or Stdio transport
                    _func = self.handler.connect_to_mcp_server
                    if self.handler.sse_transport:
                        _func = self.handler.connect_to_mcp_sse_server
                        
                    session = await _func()

                    async for tool in iter_to_aiter(message.tool_calls):
                        if tool.tool_type == 'function':
                            res = await session.call_tool(tool.name, arguments=tool.arguments or {})
                            parsed = await self.output_parser.parse(res) if self.output_parser else res
                            results.append(parsed)
                    await self.handler.cleanup()
                else:
                    # General handler function calls
                    async for tool in iter_to_aiter(message.tool_calls):
                        if tool.tool_type == 'function':
                            func = getattr(self.handler, tool.name, None)
                            if func and (inspect.isfunction(func) or inspect.ismethod(func)):
                                args = tool.arguments or {}
                                logger.debug(f"Calling {tool.name} with args {args}")
                                result = await func(**args) if inspect.iscoroutinefunction(
                                    func) else await sync_to_async(func, **args)
                                parsed = await self.output_parser.parse(result) if self.output_parser else result
                                results.append(parsed)
                            else:
                                logger.warning(f"Handler method not found: {tool.name}")
            else:
                # If no tool call, treat as LLM-generated content
                results.append(message.content)

        return results
