import inspect
import logging
import typing

from agentx.exceptions import ToolError
from agentx.handler.base import BaseHandler
from agentx.handler.exceptions import InvalidHandler
from agentx.llm import LLMClient, ChatCompletionParams
from agentx.prompt import PromptTemplate
from agentx.utils.helper import iter_to_aiter, sync_to_async
from agentx.utils.parsers.base import BaseParser

logger = logging.getLogger(__name__)


class Engine:

    def __init__(
            self,
            *,
            handler: BaseHandler,
            llm: LLMClient,
            prompt_template: PromptTemplate,
            tools: list[dict] | list[str] | None = None,
            output_parser: BaseParser | None = None
    ):
        self.handler = handler
        self.llm = llm
        self.prompt_template = prompt_template
        self.tools = tools
        self.output_parser = output_parser

    async def __funcs_props(self, funcs: list[str] | list[dict]) -> list[dict]:
        _funcs_props: list[dict] = []
        async for _func_name in iter_to_aiter(funcs):
            _func = None
            if isinstance(_func_name, str):
                _func_name = _func_name.split('.')[-1]
                _func = getattr(self.handler, _func_name)
                logger.debug(f"Func Name => {_func_name}, Func => {_func}")
            else:
                # TODO: Needs to fix this for tools contains list of dict
                pass
            if inspect.ismethod(_func) or inspect.isfunction(_func):
                logger.debug(f"{_func_name} is function!")
                _funcs_props.append(await self.llm.get_tool_json(func=_func))
        return _funcs_props

    async def _construct_tools(self) -> list[dict]:
        funcs = dir(self.handler)
        logger.debug(f"Handler Funcs => {funcs}")
        if not funcs:
            raise InvalidHandler(str(self.handler))

        _tools: list[dict] = []
        if self.tools:
            _tools = await self.__funcs_props(funcs=self.tools)
        if not _tools:
            _tools = await self.__funcs_props(funcs=funcs)
        return _tools

    async def start(
            self,
            input_prompt: str,
            pre_result: str | None = None,
            **kwargs
    ) -> list[typing.Any]:

        if pre_result:
            input_prompt = f'{input_prompt}\n\n{pre_result}'

        if not kwargs:
            kwargs = {}
        prompt_messages = await self.prompt_template.get_messages(
            input_prompt=input_prompt,
            **kwargs
        )
        logger.debug(f"Prompt message => {prompt_messages}")
        tools = await self._construct_tools()
        logger.debug(f"Handler Tools => {tools}")
        chat_completion_params = ChatCompletionParams(
            messages=prompt_messages,
            tools=tools
        )
        logger.debug(f"Chat completion params => {chat_completion_params.model_dump_json(exclude_none=True)}")
        messages = await self.llm.afunc_chat_completion(
            chat_completion_params=chat_completion_params
        )
        logger.debug(f"Func chat completion => {messages}")
        if not messages:
            raise ToolError("Tool not found for the inputs!")

        results = []
        async for message in iter_to_aiter(messages):
            if message.tool_calls:
                async for tool in iter_to_aiter(message.tool_calls):
                    if tool.tool_type == 'function':
                        func = getattr(self.handler, tool.name)
                        if func and (inspect.ismethod(func) or inspect.isfunction(func)):
                            _kwargs = tool.arguments or {}
                            if inspect.iscoroutinefunction(func):
                                res = await func(**_kwargs)
                            else:
                                res = await sync_to_async(func, **_kwargs)

                            if res:
                                if not self.output_parser:
                                    results.append(res)
                                else:
                                    results.append(await self.output_parser.parse(res))
            else:
                results.append(message.content)
        return results
