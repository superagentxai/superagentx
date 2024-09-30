import asyncio
from typing import Literal

from agentx.agent import Agent
from agentx.constants import SEQUENCE
from agentx.utils.helper import iter_to_aiter


class AgentXPipe:

    def __init__(
            self,
            *,
            goal: str | None = None,
            role: str | None = None,
            prompt: str | None = None,
            name: str | None = None,
            description: str | None = None
    ):
        self.goal = goal
        self.role = role
        self.prompt = prompt
        self.name = name
        self.description = description
        self.agents: list[Agent | list[Agent]] = []

    async def add(
            self,
            *agents: Agent,
            execute_type: Literal['SEQUENCE', 'PARALLEL'] = 'SEQUENCE'
    ):
        if execute_type == SEQUENCE:
            self.agents += agents
        else:
            self.agents.append(list(agents))

    async def flow(self):
        # TODO: Implement actual pipe flow 🤔
        results = []
        async for _agents in iter_to_aiter(self.agents):
            if isinstance(_agents, list):
                _res = await asyncio.gather(
                    *[_agent.execute() async for _agent in iter_to_aiter(_agents)]
                )
            else:
                _res = await _agents.execute()
            results.append(_res)
        # TODO: Needs to fix for pipe out
        # TODO: Needs to verify its goal after all set
        # TODO: Needs to retry if it fails
        return results
