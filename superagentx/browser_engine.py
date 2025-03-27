import inspect
import logging
import typing
from abc import ABC

from superagentx.base_engine import BaseEngine
from superagentx.computer_use.browser.browser import Browser, BrowserContext, BrowserConfig
from superagentx.exceptions import ToolError
from superagentx.handler.base import BaseHandler
from superagentx.handler.browser import BrowserHandler
from superagentx.handler.exceptions import InvalidHandler
from superagentx.llm import LLMClient, ChatCompletionParams
from superagentx.prompt import PromptTemplate
from superagentx.utils.helper import iter_to_aiter, sync_to_async
from superagentx.utils.parsers.base import BaseParser
from superagentx.constants import BROWSER_SYSTEM_MESSAGE, COT_BROWSER_SYSTEM_MESSAGE

logger = logging.getLogger(__name__)


class BrowserEngine(BaseEngine):

    def __init__(self, *args, llm: LLMClient, prompt_template: PromptTemplate, browser_instance_path: str = None,
                 browser: Browser | None = None, browser_context: BrowserContext | None = None, tools: list[dict] | list[str] | None = None, **kwargs):

        super().__init__(*args, **kwargs)
        self.llm = llm
        self.tools = tools
        if browser is not None:
            self.browser = browser
        elif browser_instance_path:
            self.browser = Browser(config=BrowserConfig(chrome_instance_path=browser_instance_path))
        else:
            self.browser = Browser()

        self.browser_context = (
            browser_context if browser_context else
            (BrowserContext(browser=self.browser,
                            config=self.browser.config.new_context_config) if self.browser else None)
        )

        self.handler = BrowserHandler(self.llm, self.browser_context)

    async def  __funcs_props(
            self,
            funcs: list[str]
    ) -> list[dict]:
        _funcs_props: list[dict] = []
        async for _func_name in iter_to_aiter(funcs):
            _func_name = _func_name.split('.')[-1]
            _func = getattr(self.handler, _func_name)
            logger.debug(f"Func Name : {_func_name}, Func : {_func}")
            if inspect.ismethod(_func) or inspect.isfunction(_func):
                logger.debug(f"{_func_name} is function!")
                _funcs_props.append(await self.llm.get_tool_json(func=_func))
        return _funcs_props

    async def _construct_tools(self) -> list[dict]:
        funcs = self.handler.tools or dir(self.handler)
        logger.debug(f"Handler Funcs : {funcs}")
        if not funcs:
            raise InvalidHandler(str(self.handler))

        _tools: list[dict] = []
        if self.tools:
            _tools = await self.__funcs_props(funcs=self.tools)
        if not _tools:
            _tools = await self.__funcs_props(funcs=funcs)
        return _tools

    async def start(self,
                    input_prompt: str,
                    pre_result: str | None = None,
                    old_memory: list[dict] | None = None,
                    conversation_id: str | None = None,
                    **kwargs):

        funcs = self.handler.tools or dir(self.handler)
        _tools = await self.__funcs_props(funcs=funcs)
        logger.info(f"Handler Funcs : {funcs}")
        logger.info(f"Handler Tools List : {_tools}")

        # page = await self.browser_context.get_current_page()
        # await page.goto('https://en.wikipedia.org/wiki/Banana')
        # state = await self.browser_context.get_state()
        # print(f"State.... {state}")
        # print(state.element_tree.clickable_elements_to_string())

        msgs = [
            {"role": "system", "content": BROWSER_SYSTEM_MESSAGE},
            {"role": "user",
             "content": "Your ultimate task is: \"Find the latest Agentic AI news from twitter and write a summary "
                        "about that post\". If you"
                        "achieved your ultimate task, stop everything and use the done action in the next step to "
                        "complete the task. If not, continue as usual."},
            {"role": "user", "content": "Example output"}
        ]
        tools = await self._construct_tools()
        chat_completion_params = ChatCompletionParams(
            messages=msgs,
            tools=tools
        )

        messages = await self.llm.afunc_chat_completion(
            chat_completion_params=chat_completion_params
        )
        logger.info(f"Func Chat Completion : {messages[0].content}")
        if not messages:
            raise ToolError("Tool not found for the inputs!")

        results = []
        async for message in iter_to_aiter(messages):
            if message.tool_calls:
                async for tool in iter_to_aiter(message.tool_calls):
                    if tool.tool_type == 'function':
                        logger.debug(f'Checking tool function : {self.handler.__class__}.{tool.name}')
                        func = getattr(self.handler, tool.name)
                        if func and (inspect.ismethod(func) or inspect.isfunction(func)):
                            _kwargs = tool.arguments or {}
                            logger.debug(
                                f'Executing tool function : {self.handler.__class__}.{tool.name}, '
                                f'With arguments : {_kwargs}'
                            )
                            if inspect.iscoroutinefunction(func):
                                res = await func(**_kwargs)
                            else:
                                res = await sync_to_async(func, **_kwargs)

                            logger.info(f'Tool function res : {res}')
                            results.append(message.content)
                            logger.info(f'Tool function result : {results}')

        return results
