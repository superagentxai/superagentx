import asyncio
import json
import logging
import uuid
from typing import Literal, Any

from pydantic import BaseModel

from agentx.agent.engine import Engine
from agentx.constants import SEQUENCE
from agentx.llm import LLMClient, ChatCompletionParams
from agentx.prompt import PromptTemplate
from agentx.utils.helper import iter_to_aiter

logger = logging.getLogger(__name__)

_GOAL_PROMPT_TEMPLATE = """Review the given output context and make sure

the following goal is achieved.

Goal: {goal}

Query_Instruction: {query_instruction}

Output_Context : {output_context}

Feedback: {feedback}

Output_Format: {output_format}

Follow the instructions step-by-step carefully and act upon.

Review the Output_Context based on the given Goal with Query_Instruction and set the result in the below mentioned result.

Answer should be based on the given output context. Do not try answer by your own.

Make sure generate the result based on the given output format if provided. 

{{
    reason: Set the reason for result,
    result: Set this based on given output format if output format given. Otherwise set the result as it is.,
    is_goal_satisfied: 'True' if result satisfied based on the given goal. Otherwise set as 'False'. Set only 'True' or 'False' boolean.
}}

Always generate the JSON output.
"""


class GoalResult(BaseModel):
    reason: str
    result: Any
    is_goal_satisfied: bool


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
            query_instruction: str,
            results: list[Any]
    ) -> GoalResult:
        prompt_message = await self.prompt_template.get_messages(
            input_prompt=_GOAL_PROMPT_TEMPLATE,
            goal=self.goal,
            query_instruction=query_instruction,
            output_context=results,
            feedback="",
            output_format=self.output_format or ""
        )
        chat_completion_params = ChatCompletionParams(
            messages=prompt_message
        )
        messages = await self.llm.achat_completion(
            chat_completion_params=chat_completion_params
        )
        logger.info(f"Goal pre result => {messages}")
        if messages and messages.choices:
            for choice in messages.choices:
                if choice and choice.message:
                    _res = choice.message.content
                    _res = json.loads(_res)
                    return GoalResult(**_res)

    async def _execute(
            self,
            query_instruction: str
    ):
        results = []
        async for _engines in iter_to_aiter(self.engines):
            if isinstance(_engines, list):
                _res = await asyncio.gather(
                    *[_engine.start(input_prompt=query_instruction) async for _engine in iter_to_aiter(_engines)]
                )
            else:
                _res = await _engines.start(input_prompt=query_instruction)
            results.append(_res)
        logger.debug(f"Engine results =>\n{results}")
        final_result = await self._verify_goal(
            results=results,
            query_instruction=query_instruction
        )
        logger.info(f"Final Result =>\n, {final_result}")
        return final_result

    async def execute(
            self,
            query_instruction: str
    ):
        for _retry in range(1, self.max_retry+1):
            logger.info(f"Agent retry {_retry}")
            _goal_result = await self._execute(
                query_instruction=query_instruction
            )
            if _goal_result.is_goal_satisfied:
                return _goal_result
        logger.warning(f"Done agent max retry {self.max_retry}!")
