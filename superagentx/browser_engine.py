import inspect
import json
import logging
from datetime import datetime
from typing import TypeVar

import yaml

from superagentx.base_engine import BaseEngine
from superagentx.computer_use.browser.browser import Browser, BrowserContext, BrowserConfig
from superagentx.computer_use.browser.dom.views import DOMBaseNode, DOMElementNode, DOMTextNode
from superagentx.computer_use.browser.models import AgentStepInfo, ActionResult
from superagentx.constants import BROWSER_SYSTEM_MESSAGE
from superagentx.handler.browser import BrowserHandler
from superagentx.handler.exceptions import InvalidHandler
from superagentx.llm import LLMClient, ChatCompletionParams
from superagentx.prompt import PromptTemplate
from superagentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)


class ElementTreeSerializer:
    @staticmethod
    def dom_element_node_to_json(element_tree: DOMElementNode) -> dict:
        def node_to_dict(node: DOMBaseNode) -> dict:
            if isinstance(node, DOMTextNode):
                return {'type': 'text', 'text': node.text}
            elif isinstance(node, DOMElementNode):
                return {
                    'type': 'element',
                    'tag_name': node.tag_name,
                    'attributes': node.attributes,
                    'highlight_index': node.highlight_index,
                    'children': [node_to_dict(child) for child in node.children],
                }
            return {}

        return node_to_dict(element_tree)


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
            **kwargs
    ):

        super().__init__(*args, **kwargs)
        self.llm = llm
        self.tools = tools
        self.prompt_template = prompt_template
        self.n_steps = 1
        self.max_steps = max_steps
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
        self.msgs = []

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

    @staticmethod
    async def _get_user_message(state, step_info, action_result, use_vision: bool = True):
        include_attributes = []
        elements_text = state.element_tree.clickable_elements_to_string(
            include_attributes=include_attributes)

        has_content_above = (state.pixels_above or 0) > 0
        has_content_below = (state.pixels_below or 0) > 0

        if elements_text != '':
            if has_content_above:
                elements_text = (
                    f'... {state.pixels_above} pixels above - scroll or extract content to see more ...\n{elements_text}'
                )
            else:
                elements_text = f'[Start of page]\n{elements_text}'
            if has_content_below:
                elements_text = (
                    f'{elements_text}\n... {state.pixels_below} pixels below - scroll or extract content to see more ...'
                )
            else:
                elements_text = f'{elements_text}\n[End of page]'
        else:
            elements_text = 'empty page'

        if step_info:
            step_info_description = f'Current step: {step_info.step_number + 1}/{step_info.max_steps}'
        else:
            step_info_description = ''
        time_str = datetime.now().strftime('%Y-%m-%d %H:%M')
        step_info_description += f'Current date and time: {time_str}'

        state_description = f"""
[Task history memory ends]
[Current state starts here]
The following is one-time information - if you need to remember it write it to memory:
Current url: {state.url}
Available tabs:
{state.tabs}
Interactive elements from top layer of the current page inside the viewport:
{elements_text}
{step_info_description}
"""

        if action_result:
            for i, result in enumerate(action_result):
                if result.extracted_content:
                    state_description += f'\nAction result {i + 1}/{len(action_result)}: {result.extracted_content}'
                if result.error:
                    # only use last line of error
                    error = result.error.split('\n')[-1]
                    state_description += f'\nAction error {i + 1}/{len(action_result)}: ...{error}'

        if state.screenshot and use_vision:
            return {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": state_description
                }, {
                    'type': 'image_url',
                    'image_url': {'url': f'data:image/png;base64,{state.screenshot}'},  # , 'detail': 'low'
                }
                ]
            }
        return {
            "role": "user",
            "content": state_description
        }

    async def _remove_last_state_message(self, messages) -> None:
        """Remove last state message from history"""
        if len(messages) > 2 and isinstance(messages[-1], dict):
            del self.msgs[-1]

    async def start(self,
                    input_prompt: str,
                    pre_result: str | None = None,
                    old_memory: list[dict] | None = None,
                    conversation_id: str | None = None,
                    **kwargs):
        results = []

        self.msgs = [
            {"role": "system", "content": f"{BROWSER_SYSTEM_MESSAGE}\n\nNote:\nEnsure to first build the step by step "
                                          f"process, once you build the steps then execute the steps use click event "
                                          f"for every step to need. Don't give the duplicate json."},
            {"role": "user",
             "content": f"Your ultimate task is: {input_prompt} about that post\". If you"
                        "achieved your ultimate task, stop everything and use the done action in the next step to "
                        "complete the task. If not, continue as usual."},
            {"role": "user", "content": "Example output"},
            {"role": "assistant", "content": ""}
        ]
        result = None
        async for step in iter_to_aiter(range(self.max_steps)):
            logger.info(f'Step {self.n_steps}')
            state = await self.browser_context.get_state()
            page = await self.browser_context.get_current_page()
            step_info = AgentStepInfo(step_number=step, max_steps=self.max_steps)
            state_msg = await self._get_user_message(state=state, step_info=step_info, action_result=result)
            self.msgs.append(state_msg)
            funcs = self.handler.tools or dir(self.handler)
            _tools = await self.__funcs_props(funcs=funcs)
            logger.debug(f"Handler Funcs : {funcs}")
            logger.debug(f"Handler Tools List : {_tools}")

            tools = await self._construct_tools()

            chat_completion_params = ChatCompletionParams(
                messages=self.msgs,
                tools=tools
            )
            chat_completion_params.temperature = 0
            chat_completion_params.response_format = {"type": "json_object"}
            messages = await self.llm.afunc_chat_completion(
                chat_completion_params=chat_completion_params
            )
            logger.info(messages)
            res = messages[0].content
            res = json.loads(res)
            await self._remove_last_state_message(self.msgs)
            self.msgs.append({
                "role": "assistant",
                "content": f"{yaml.dump(res)}"
            })
            actions = res.get("action")
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
                                    logger.info("Yes")
                                    _engine_res = await func(**_kwargs)
                                    await self.browser_context.get_current_page()

                                # self.msgs.append({
                                #     "role": "user",
                                #     "content": str(_kwargs)
                                # })
                                _value = list(_kwargs.values())
                                if _engine_res.extracted_content:
                                    result = [ActionResult(
                                        extracted_content=_engine_res.extracted_content
                                    )]
                                else:
                                    result = [ActionResult(
                                        error=_engine_res.error
                                    )]
                                self.n_steps += 1
                            except Exception as ex:
                                result = [ActionResult(
                                    error=f"{ex}"
                                )]
                                self.n_steps += 1
                    else:
                        results.append(res)
                        await self.browser_context.close()
                        await self.browser.close()
                        return results
            # logger.info(f"Func Chat Completion : {messages}")

        # funcs = self.handler.tools or dir(self.handler)
        # _tools = await self.__funcs_props(funcs=funcs)
        # logger.info(f"Handler Funcs : {funcs}")
        # logger.info(f"Handler Tools List : {_tools}")
        #
        # # page = await self.browser_context.get_current_page()
        # # await page.goto('https://en.wikipedia.org/wiki/Banana')
        # # state = await self.browser_context.get_state()
        # # print(f"State.... {state}")
        # # print(state.element_tree.clickable_elements_to_string())
        #
        # msgs = [
        #     {"role": "system", "content": f"{BROWSER_SYSTEM_MESSAGE}\n\nNote:\nEnsure to first build the step by step "
        #                                   f"process, once you build the steps then execute the steps use click event "
        #                                   f"for every step to need. Don't give the duplicate json."},
        #     {"role": "user",
        #      "content": f"Your ultimate task is: {input_prompt} about that post\". If you"
        #                 "achieved your ultimate task, stop everything and use the done action in the next step to "
        #                 "complete the task. If not, continue as usual."},
        #     {"role": "user", "content": "Example output"},
        #     {"assistant": ""}
        # ]
        # tools = await self._construct_tools()
        #
        # chat_completion_params = ChatCompletionParams(
        #     messages=msgs,
        #     tools=tools
        # )
        # chat_completion_params.temperature = 0
        # chat_completion_params.response_format = {"type": "json_object"}
        # messages = await self.llm.afunc_chat_completion(
        #     chat_completion_params=chat_completion_params
        # )
        # if not messages:
        #     raise ToolError("Tool not found for the inputs!")
        # logger.info(f"Func Chat Completion : {messages[0].content}")
        #
        # results = []
        #
        # async def automation(_messages):
        #     async for _message in iter_to_aiter(_messages):
        #         _dict_data = json.loads(_message.content)
        #         _actions = _dict_data.get("action")
        #         async for _tool in iter_to_aiter(_actions):
        #             _funcs = list(_tool.keys())
        #             if _funcs:
        #                 _tool_name = _funcs[0]
        #                 if _tool_name == "done":
        #                     return _tool.get(_tool_name)
        #                 _func = getattr(self.handler, _tool_name)
        #                 if _func and (inspect.ismethod(_func) or inspect.isfunction(_func)):
        #                     logger.debug(f'Checking tool function : {self.handler.__class__}.{_tool_name}')
        #                     _kwargs = _tool.get(_tool_name) or {}
        #                     logger.debug(
        #                         f'Executing tool function : {self.handler.__class__}.{_tool_name}, '
        #                         f'With arguments : {_kwargs}'
        #                     )
        #                     if inspect.iscoroutinefunction(_func):
        #                         await _func(**_kwargs)
        #                         await asyncio.sleep(1)
        #                         await self.browser_context.get_current_page()
        #
        # async for message in iter_to_aiter(messages):
        #     dict_data = json.loads(message.content)
        #     actions = dict_data.get("action")
        #     async for tool in iter_to_aiter(actions):
        #         async for key, value in iter_to_aiter(tool.items()):
        #             tool_name = key
        #             func = getattr(self.handler, tool_name)
        #             if func and (inspect.ismethod(func) or inspect.isfunction(func)):
        #                 logger.debug(f'Checking tool function : {self.handler.__class__}.{tool_name}')
        #                 _kwargs = tool.get(tool_name) or {}
        #                 logger.debug(
        #                     f'Executing tool function : {self.handler.__class__}.{tool_name}, '
        #                     f'With arguments : {_kwargs}'
        #                 )
        #                 if inspect.iscoroutinefunction(func):
        #                     await func(**_kwargs)
        #                     await asyncio.sleep(1)
        #                     await self.browser_context.get_current_page()
        #                     status = True
        #                     while status:
        #                         state = await self.browser_context.get_state()
        #                         dom = await self._web(self.browser_context, state)
        #                         msgs.append({
        #                             "role": "system",
        #                             "content": messages[0].content
        #                         })
        #                         msgs.append({
        #                             "role": "user",
        #                             "content": f"Dom Element:\n\n{dom}"
        #                         })
        #                         logger.info(msgs)
        #                         chat_completion_params.messages = msgs
        #                         chat_completion_params.tools = tools
        #                         chat_completion_params.response_format = {"type": "json_object"}
        #                         messages = await self.llm.afunc_chat_completion(
        #                             chat_completion_params=chat_completion_params
        #                         )
        #                         logger.info(f"Func Chat Completion : {messages}")
        #                         if not messages[0].content and messages[0].tool_calls:
        #                             _tools = messages[0].tool_calls
        #                             messages[0].content = [tool_call async for tool_call in iter_to_aiter(_tools)]
        #
        #                         result = await automation(messages)
        #                         if result:
        #                             results.append(result)
        #                             await self.browser_context.close()
        #                             await self.browser.close()
        #                             status = False

        # return []
