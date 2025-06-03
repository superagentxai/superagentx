import asyncio
import inspect
import json
import logging
import os
import re
import uuid
import aiopath
from typing import TypeVar, Any

import pathlib
from pydantic import BaseModel

from superagentx.base import BaseEngine
from superagentx.computer_use.browser.models import StepInfo, ToolResult
from superagentx.computer_use.constants import EXAMPLE_DATA
from superagentx.computer_use.utils import (
    get_user_message,
    show_toast,
    SYSTEM_MESSAGE,
    log_response,
    manipulate_string
)
from superagentx.handler.exceptions import InvalidHandler
from superagentx.llm import LLMClient, ChatCompletionParams
from superagentx.prompt import PromptTemplate
from superagentx.utils.helper import iter_to_aiter, rm_trailing_spaces, sync_to_async
from superagentx.computer_use.browser.models import InputTextParams, GoToUrl, ToastConfig

logger = logging.getLogger(__name__)

Context = TypeVar('Context')


class BrowserEngine(BaseEngine):

    def __init__(
            self,
            *args,
            llm: LLMClient,
            prompt_template: PromptTemplate,
            browser_instance_path: str = None,
            browser: Any | None = None,
            browser_context: Any | None = None,
            tools: list[dict] | list[str] | None = None,
            max_steps: int = 100,
            take_screenshot: bool = False,
            screenshot_path: str | pathlib.Path | None = None,
            sensitive_data: dict | None = None,
            toast_config: ToastConfig | None = None,
            **kwargs
    ):

        super().__init__(*args, **kwargs)
        from superagentx.computer_use.browser.browser import Browser, BrowserContext, BrowserConfig
        from superagentx.handler.browser import BrowserHandler
        self.llm = llm
        self.tools = tools
        self.prompt_template = prompt_template
        self.n_steps = 1
        self.max_steps = max_steps
        self.take_screenshot = take_screenshot
        self.async_mode = self.llm.llm_config_model.async_mode
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
        self.sensitive_data = sensitive_data
        self.toast_config = toast_config
        self.previous_state = None
        self.extract_result = []

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

    async def _remove_last_state_message(self, messages: list) -> None:
        """Remove last state message from history"""
        if len(messages) > 2 and isinstance(messages[-1], dict):
            del self.msgs[-1]

    @staticmethod
    def _replace_sensitive_data(
            params: BaseModel,
            sensitive_data: dict[str, Any]
    ) -> BaseModel:
        """Replaces the sensitive data in the params"""
        # if there are any str with <secret>placeholder</secret> in the params, replace them with the actual value from
        # sensitive_data

        secret_pattern = re.compile(r'<secret>(.*?)</secret>')

        # Set to track all missing placeholders across the full object
        all_missing_placeholders = set()

        def replace_secrets(value):
            if isinstance(value, str):
                matches = secret_pattern.findall(value)

                for placeholder in matches:
                    if placeholder in sensitive_data and sensitive_data[placeholder]:
                        value = value.replace(
                            f'<secret>{placeholder}</secret>',
                            sensitive_data[placeholder]
                        )
                    else:
                        # Keep track of missing placeholders
                        all_missing_placeholders.add(placeholder)
                    # Don't replace the tag, keep it as is

                return value
            elif isinstance(value, dict):
                return {k: replace_secrets(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [replace_secrets(v) for v in value]
            return value

        params_dump = params.model_dump()
        processed_params = replace_secrets(params_dump)

        # Log a warning if any placeholders are missing
        if all_missing_placeholders:
            logger.warning(
                f'Missing or empty keys in sensitive_data dictionary: {", ".join(all_missing_placeholders)}'
            )

        return type(params).model_validate(processed_params)

    async def _action_execute(
            self,
            actions: dict,
            page: Any,
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
                        if self.sensitive_data and tool_name == "go_to_url":
                            validated_params = GoToUrl(**_kwargs)
                            _kwargs = await sync_to_async(
                                self._replace_sensitive_data,
                                validated_params,
                                self.sensitive_data
                            )
                            _kwargs = _kwargs.model_dump()
                        if self.sensitive_data and tool_name == "input_text":
                            _kwargs["has_sensitive"] = True
                            validated_params = InputTextParams(**_kwargs)
                            _kwargs = await sync_to_async(
                                self._replace_sensitive_data,
                                validated_params,
                                self.sensitive_data
                            )
                            _kwargs = _kwargs.model_dump()
                        logger.debug(
                            f'Executing tool function : {self.handler.__class__}.{tool_name}, '
                            f'With arguments : {_kwargs}'
                        )
                        try:
                            _engine_res = None
                            if inspect.iscoroutinefunction(func):
                                await show_toast(
                                    page=page,
                                    message=current_state.get("next_goal"),
                                    toast_config=self.toast_config,
                                    duration=1000
                                )
                                _engine_res = await func(**_kwargs)
                            _value = list(_kwargs.values())
                            if tool_name == "extract_content":
                                self.extract_result.append(_engine_res)
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
        counter = 0
        self.extract_result = []
        async for step in iter_to_aiter(range(self.max_steps)):
            logger.info(f'Step {self.n_steps}')
            await asyncio.sleep(1)
            state = await self.browser_context.get_state(cache_clickable_elements_hashes=True)
            page = await self.browser_context.get_current_page()
            step_info = StepInfo(step_number=step, max_steps=self.max_steps)
            if self.extract_result:
                self.msgs.append({
                    "role": "user",
                    "content": f"Step {step-1} Result: {self.extract_result}"
                })
            state_msg = await get_user_message(state=state, step_info=step_info, action_result=result)
            self.msgs.append(state_msg.get('msg'))
            if self.previous_state == state_msg.get('element_text'):
                counter += 1
                logger.info(f"Retry Count: {counter}")
                if counter >= 5:
                    _retry_fail = {
                        "role": "user",
                        "content": f"Tried this step {counter} times. So done fail proces and say the reason."
                    }
                    self.msgs.append(_retry_fail)
                    counter = 0
            else:
                self.previous_state = state_msg.get('element_text')
                counter = 0

            chat_completion_params = ChatCompletionParams(
                messages=self.msgs,
                temperature=0
            )
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
            logger.info(f"Response: {res}")
            actions = res.get("action")
            current_state = res.get("current_state")
            result = await self._action_execute(
                actions=actions,
                page=page,
                current_state=current_state
            )

            if result:
                _result = result[0]
                if _result.is_done:
                    response = res.get("action", [])[0].get("done", {}).get("text")
                    if isinstance(response, (list, dict)):
                        response = f"Process Success Executed"
                    await show_toast(
                        page=page,
                        message=response,
                        duration=4000,
                        toast_config=self.toast_config
                    )
                    await asyncio.sleep(4)
                    if self.screenshot_path:
                        file_path = aiopath.Path(self.screenshot_path)
                        if await file_path.is_dir():
                            file_path = f"{self.screenshot_path.strip('/')}/img_{uuid.uuid4().hex}.jpg"
                        await self.browser_context.take_screenshot(
                            path=file_path
                        )
                        await show_toast(
                            page=await self.browser_context.get_current_page(),
                            message="Screen Captured",
                            toast_config=self.toast_config
                        )
                        await asyncio.sleep(2)
                    await self.browser_context.close()
                    await self.browser.close()
                    results.append(res)
                    return results

    async def start(
            self,
            input_prompt: str,
            pre_result: str | None = None,
            old_memory: list[dict] | None = None,
            conversation_id: str | None = None,
            **kwargs
    ) -> list:

        msgs = [
            {"role": "user",
             "content": f"Your ultimate task is: {input_prompt} about that post\". If you"
                        "achieved your ultimate task, stop everything and use the done action in the next step to "
                        "complete the task. If not, continue as usual."},
            {"role": "user", "content": "Example output"},
            {"role": "assistant", "content": EXAMPLE_DATA}
        ]
        if self.sensitive_data:
            info = f'Here are placeholders for sensitive data: {list(self.sensitive_data.keys())}'
            info += '\nTo use them, write <secret>the placeholder name</secret>. If password is wrong done the process.'
            msgs.append({
                "role": "user",
                "content": info
            })
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
