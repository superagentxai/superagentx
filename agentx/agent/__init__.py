import asyncio
import uuid
from typing import Literal, Any

from agentx.agent.engine import Engine
from agentx.constants import SEQUENCE, PARALLEL
from agentx.llm import LLMClient, ChatCompletionParams
from agentx.utils.helper import iter_to_aiter

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

{{
    "result": {{
        Set the result based on given output format if output format given. Otherwise set the result as it is.
    }},
    "is_goal_satisfied": {{
        Set boolean 'True' if result satisfied based on the given goal. Otherwise set as 'False'. 
        Set only 'True' or 'False' boolean
    }}
}}

"""


class Agent:

    def __init__(
            self,
            *,
            goal: str,
            role: str,
            llm: LLMClient,
            input_prompt: str | None = None,
            output_format: str | None = None,
            name: str | None = None,
            description: str | None = None,
            max_retry: int = 5
    ):
        self.role = role
        self.goal = goal
        self.llm = llm
        self.input_prompt = input_prompt
        self.output_format = output_format
        self.name = name or uuid.uuid4().hex
        self.description = description
        self.max_retry = max_retry
        self.engines: list[Engine | list[Engine]] = []

    async def add(
            self,
            *engines: Engine,
            execute_type: Literal[SEQUENCE, PARALLEL] = SEQUENCE
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
        _prompt = _GOAL_PROMPT_TEMPLATE.format(
            goal=self.goal,
            output_context=results,
            feedback="",
            output_format=self.output_format or ""
        )
        chat_completion_params = ChatCompletionParams(
            messages=_prompt
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
        final_result = await self._verify_goal(results=results)
        print("Final Result =>\n", final_result)
        # TODO: Needs to fix for agent out
        # TODO: Needs to verify its goal after all set
        # TODO: Needs to retry if it fails
        return results
