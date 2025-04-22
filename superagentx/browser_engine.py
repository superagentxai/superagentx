import asyncio
import inspect
import json
import logging
import os
import pathlib
import typing
import uuid
from typing import TypeVar

from playwright.async_api import Page

from superagentx.base_engine import BaseEngine
from superagentx.computer_use.browser.browser import Browser, BrowserContext, BrowserConfig
from superagentx.computer_use.browser.models import StepInfo, ToolResult
from superagentx.computer_use.utils import get_user_message, show_toast, SYSTEM_MESSAGE, log_response, manipulate_string
from superagentx.handler.browser import BrowserHandler
from superagentx.handler.exceptions import InvalidHandler
from superagentx.llm import LLMClient, ChatCompletionParams
from superagentx.prompt import PromptTemplate
from superagentx.utils.helper import iter_to_aiter, rm_trailing_spaces, sync_to_async

logger = logging.getLogger(__name__)

Context = TypeVar('Context')


class BrowserEngine(BaseEngine):

    def __init__(
            self,
            *args,
            llm: LLMClient,
            prompt_template: PromptTemplate,
            browser_instance_path: str = None,
            browser: Browser | None = None,
            browser_context: BrowserContext | None = None,
            tools: list[dict] | list[str] | None = None,
            max_steps: int = 100,
            take_screenshot: bool = False,
            screenshot_path: typing.Optional[typing.Union[str, pathlib.Path]] = None,
            **kwargs
    ):

        super().__init__(*args, **kwargs)
        self.llm = llm
        self.tools = tools
        self.prompt_template = prompt_template
        self.n_steps = 1
        self.max_steps = max_steps
        self.take_screenshot = take_screenshot
        if browser is not None:
            self.browser = browser
        elif browser_instance_path:
            self.browser = Browser(
                config=BrowserConfig(
                    chrome_instance_path=browser_instance_path
                )
            )
        else:
            self.browser = Browser()

        self.browser_context = (
            browser_context if browser_context else
            (
                BrowserContext(
                    browser=self.browser,
                    config=self.browser.config.new_context_config
                ) if self.browser else None
            )
        )

        self.handler = BrowserHandler(self.llm, self.browser_context)
        self.msgs: list = SYSTEM_MESSAGE
        self.screenshot_path = screenshot_path
        if self.take_screenshot:
            if not self.screenshot_path:
                self.screenshot_path = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "sagentx_screenshot_path"
                )

    async def __funcs_props(
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

    async def _remove_last_state_message(self, messages) -> None:
        """Remove last state message from history"""
        if len(messages) > 2 and isinstance(messages[-1], dict):
            del self.msgs[-1]

    async def _action_execute(
            self,
            actions: dict,
            page: Page,
            current_state: dict
    ) -> list[ToolResult]:
        async for tool in iter_to_aiter(actions):
            async for key, value in iter_to_aiter(tool.items()):
                tool_name = key
                if key != "done":
                    func = getattr(self.handler, tool_name)
                    if func and (inspect.ismethod(func) or inspect.isfunction(func)):
                        logger.debug(f'Checking tool function : {self.handler.__class__}.{tool_name}')
                        _kwargs = tool.get(tool_name) or {}
                        logger.debug(
                            f'Executing tool function : {self.handler.__class__}.{tool_name}, '
                            f'With arguments : {_kwargs}'
                        )
                        try:
                            _engine_res = None
                            if inspect.iscoroutinefunction(func):
                                await show_toast(page, current_state.get("next_goal"))
                                _engine_res = await func(**_kwargs)
                            _value = list(_kwargs.values())
                            if _engine_res.extracted_content:
                                result = [ToolResult(
                                    extracted_content=_engine_res.extracted_content
                                )]
                            else:
                                result = [ToolResult(
                                    error=_engine_res.error
                                )]
                            self.n_steps += 1
                            return result
                        except Exception as ex:
                            result = [ToolResult(
                                error=f"{ex}"
                            )]
                            self.n_steps += 1
                            return result
                else:
                    result = [ToolResult(
                        is_done=True
                    )]
                    return result

    async def _execute(self) -> list:
        result = None
        results = []
        async for step in iter_to_aiter(range(self.max_steps)):
            logger.info(f'Step {self.n_steps}')
            state = await self.browser_context.get_state()
            page = await self.browser_context.get_current_page()
            step_info = StepInfo(step_number=step, max_steps=self.max_steps)
            state_msg = await get_user_message(state=state, step_info=step_info, action_result=result)
            self.msgs.append(state_msg)

            chat_completion_params = ChatCompletionParams(
                messages=self.msgs
            )
            chat_completion_params.temperature = 0
            chat_completion_params.response_format = {"type": "json_object"}
            messages = await self.llm.afunc_chat_completion(
                chat_completion_params=chat_completion_params
            )
            
            if not messages:
                return results
            res = messages[0].content
            res = await sync_to_async(manipulate_string, res)
            res = json.loads(res)
            await log_response(res)
            await self._remove_last_state_message(self.msgs)
            self.msgs.append({
                "role": "assistant",
                "content": f"{res}"
            })
            actions = res.get("action")
            current_state = res.get("current_state")
            result = await self._action_execute(
                actions=actions,
                page=page,
                current_state=current_state
            )
            if result:
                if result[0].is_done:
                    await show_toast(
                        page,
                        res.get("action", [])[0].get("done", {}).get("text", ""),
                        4000
                    )
                    await self.perform_task()
                    await self.browser_context.close()
                    await self.browser.close()
                    results.append(res)
                    return results

    async def _take_screenshot_task(self):
        # Taking the screenshot (asynchronous)
        await self.browser_context.take_screenshot(path=f"{self.screenshot_path}/img_{uuid.uuid4().hex}.jpg")
        await show_toast(
            page=await self.browser_context.get_current_page(),
            message=f"Screenshot Saved in {self.screenshot_path}/img_{uuid.uuid4().hex}.jpg"
        )

    @staticmethod
    async def _sleep_task():
        # Sleep asynchronously
        await asyncio.sleep(4)

    async def perform_task(self):
        tasks = []

        # If taking a screenshot, add that task to the list
        if self.take_screenshot:
            tasks.append(self._take_screenshot_task())  # Add coroutine without awaiting it

        # Add the sleep task
        tasks.append(asyncio.create_task(self._sleep_task()))  # Create a separate task for sleep

        # Run all tasks concurrently
        await asyncio.gather(*tasks)

    async def start(self,
                    input_prompt: str,
                    pre_result: str | None = None,
                    old_memory: list[dict] | None = None,
                    conversation_id: str | None = None,
                    **kwargs):

        msgs = [
            {"role": "user",
             "content": f"Your ultimate task is: {input_prompt} about that post\". If you"
                        "achieved your ultimate task, stop everything and use the done action in the next step to "
                        "complete the task. If not, continue as usual."},
            {"role": "user", "content": "Example output"},
            {"role": "assistant", "content": ""}
        ]
        self.msgs = self.msgs + msgs
        if pre_result:
            input_prompt = f'{input_prompt}\n\n{pre_result}'

        input_prompt = f"{input_prompt}\nConversation Id: {conversation_id}"
        funcs = self.handler.tools or dir(self.handler)
        _tools = await self.__funcs_props(funcs=funcs)
        logger.debug(f"Handler Funcs : {funcs}")
        logger.debug(f"Handler Tools List : {_tools}")

        tools = await self._construct_tools()
        self.msgs.append({
            "role": "user",
            "content": f"Actions:\n\n{tools}\nSelect to correct action based on the inputs"
        })
        input_prompt = f"{input_prompt}\nConversation Id: {conversation_id}"
        prompt_messages = await self.prompt_template.get_messages(
            input_prompt=input_prompt,
            old_memory=old_memory,
            **kwargs
        )
        prompt_messages = await rm_trailing_spaces(prompt_messages)
        self.msgs = self.msgs + prompt_messages
        logger.debug(f"Prompt Message : {self.msgs}")
        result = await self._execute()
        return result
