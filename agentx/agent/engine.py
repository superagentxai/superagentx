import inspect
import typing

from agentx.handler.base import BaseHandler
from agentx.handler.exceptions import InvalidHandler
from agentx.llm import LLMClient, ChatCompletionParams
from agentx.prompt import PromptTemplate
from agentx.utils.helper import iter_to_aiter
from agentx.utils.parsers.base import BaseParser


class Engine:

    def __init__(
            self,
            *,
            handler: BaseHandler,
            llm: LLMClient,
            prompt_template: PromptTemplate,
            input_prompt: str,
            tools: list[dict] | list[str] | None = None,
            output_parser: BaseParser | None = None,
            **kwargs
    ):
        self.handler = handler
        self.llm = llm
        self.prompt_template = prompt_template
        self.input_prompt = input_prompt
        self.tools = tools
        self.output_parser = output_parser
        self.kwargs = kwargs

    @staticmethod
    async def _construct_func_props(func: typing.Callable) -> dict:
        _func_name = func.__name__
        _doc_str = inspect.getdoc(func)
        _properties = {}
        _type_hints = typing.get_type_hints(func)
        async for param, param_type in iter_to_aiter(_type_hints.items()):
            if param != 'return':
                _properties[param] = {
                    "llm_type": param_type.__name__,
                    "description": f"The {param.replace('_', ' ')}."
                }
        return {
            'type': 'function',
            'function': {
                'name': _func_name,
                'description': _doc_str,
                'parameters': {
                    "llm_type": "object",
                    "properties": _properties,
                    "required": list(_properties.keys()),
                    "additionalProperties": False
                }
            }
        }

    async def _construct_funcs_props(self, funcs: list[str]) -> list[dict]:
        _funcs_props: list[dict] = []
        async for func_name in iter_to_aiter(funcs):
            _func = getattr(self.handler, func_name)
            if inspect.isfunction(_func):
                _funcs_props.append(await self._construct_func_props(func=_func))
        return _funcs_props

    async def _construct_tools(self) -> list[dict]:
        funcs = dir(self.handler)
        if not funcs:
            raise InvalidHandler(str(self.handler))

        _tools: list[dict] = []
        if self.tools:
            async for _tool in iter_to_aiter(self.tools):
                if isinstance(_tool, str):
                    # TODO: extract func props from str func
                    pass
                elif isinstance(_tool, dict):
                    # TODO: extract func props from dict func props
                    pass
        if not _tools:
            _tools = await self._construct_funcs_props(funcs=funcs)
        return _tools

    async def start(self) -> typing.Any:
        prompt_messages = await self.prompt_template.get_messages(
            input_prompt=self.input_prompt,
            **self.kwargs
        )
        tools = await self._construct_tools()
        chat_completion_params = ChatCompletionParams(
            messages=prompt_messages,
            tools=tools
        )
        resp = await self.llm.achat_completion(
            chat_completion_params=chat_completion_params
        )
