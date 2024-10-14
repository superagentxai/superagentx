import asyncio
import uuid
from typing import Literal

from agentx.agent import Agent
from agentx.constants import SEQUENCE
from agentx.io import IOConsole
from agentx.llm.types.base import logger
from agentx.utils.helper import iter_to_aiter


class AgentXPipe:

    def __init__(
            self,
            *,
            io: IOConsole,
            goal: str | None = None,
            role: str | None = None,
            prompt: str | None = None,
            name: str | None = None,
            description: str | None = None
    ):
        self.io = io
        self.goal = goal  # TODO: will be consider in the future
        self.role = role  # TODO: will be consider in the future
        self.prompt = prompt  # TODO: will be consider in the future
        self.name = name or f'{self.__str__()}-{uuid.uuid4().hex}'
        self.description = description
        self.agents: list[Agent | list[Agent]] = []

    def __str__(self):
        return "AgentXPipe"

    def __repr__(self):
        return f"<{self.__str__()}>"

    async def add(
            self,
            *agents: Agent,
            execute_type: Literal['SEQUENCE', 'PARALLEL'] = 'SEQUENCE'
    ):
        if execute_type == SEQUENCE:
            self.agents += agents
        else:
            self.agents.append(list(agents))

    async def _flow(
            self,
            query_instruction: str
    ):
        results = []
        async for _agents in iter_to_aiter(self.agents):
            if isinstance(_agents, list):
                _res = await asyncio.gather(
                    *[_agent.execute(query_instruction=query_instruction) async for _agent in iter_to_aiter(_agents)]
                )
            else:
                _res = await _agents.execute(query_instruction=query_instruction)
            results.append(_res)
        # TODO: Needs to fix for pipe out
        # TODO: Needs to verify its goal after all set
        # TODO: Needs to retry if it fails
        return results


    async def flow(self):
        logger.debug(f"Initiating PIPe with IO {self.io}")
        while True:
            query_instruction = await self.io.read()
            result = await self._flow(
                query_instruction=query_instruction
            )
            await self.io.write(result)
