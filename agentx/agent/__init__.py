import asyncio
import logging
import uuid
from typing import Literal, Any

from agentx.agent.engine import Engine
from agentx.constants import SEQUENCE
from agentx.llm import LLMClient, ChatCompletionParams
from agentx.prompt import PromptTemplate
from agentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)

_GOAL_PROMPT_TEMPLATE = """Review the given output context and make sure

the following goal is achieved.

Goal: {goal}

Output_Context : {output_context}

Feedback: {feedback}

Output_Format: {output_format}

Follow the instructions step-by-step carefully and act upon.

Review the Output_Context based on the given goal and set the result in the below mentioned result.

Answer should be based on the given output context. Do not try answer by your own.

Make sure generate the result based on the given output format if provided. 

Set the `result` based on given output format if output format given. Otherwise set the result as it is. 
Set `is_goal_satisfied` 'True' if result satisfied based on the given goal. Otherwise set as 'False'. Set only 'True' or 'False' boolean.

"""


class Agent:

    def __init__(
            self,
            *,
            goal: str,
            role: str,
            llm: LLMClient,
            prompt_template: PromptTemplate,
            input_prompt: str | None = None,
            output_format: str | None = None,
            name: str | None = None,
            description: str | None = None,
            max_retry: int = 5
    ):
        self.role = role
        self.goal = goal
        self.llm = llm
        self.prompt_template = prompt_template
        self.input_prompt = input_prompt
        self.output_format = output_format
        self.name = name or uuid.uuid4().hex
        self.description = description
        self.max_retry = max_retry
        self.engines: list[Engine | list[Engine]] = []

    async def add(
            self,
            *engines: Engine,
            execute_type: Literal['SEQUENCE', 'PARALLEL'] = 'SEQUENCE'
    ):
        if execute_type == SEQUENCE:
            self.engines += engines
        else:
            self.engines.append(list(engines))

    async def _verify_goal(
            self,
            *,
            results: list[Any]
    ):
        prompt_message = await self.prompt_template.get_messages(
            input_prompt=_GOAL_PROMPT_TEMPLATE,
            goal=self.goal,
            output_context=results,
            feedback="",
            output_format=self.output_format or ""
        )
        chat_completion_params = ChatCompletionParams(
            messages=prompt_message,
            response_format="json_object"
        )
        messages = await self.llm.achat_completion(
            chat_completion_params=chat_completion_params
        )
        return messages

    async def execute(self):
        results = []
        async for _engines in iter_to_aiter(self.engines):
            if isinstance(_engines, list):
                _res = await asyncio.gather(
                    *[_engine.start(input_prompt=self.goal) async for _engine in iter_to_aiter(_engines)]
                )
            else:
                _res = await _engines.start(input_prompt=self.goal)
            results.append(_res)
        logger.info(f"Engine results =>\n{results}")
        final_result = await self._verify_goal(results=results)
        logger.info(f"Final Result =>\n, {final_result}")
        # TODO: Needs to fix for agent out
        # TODO: Needs to verify its goal after all set
        # TODO: Needs to retry if it fails
        return final_result
