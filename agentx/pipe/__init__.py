import asyncio
from typing import LiteralString

from agentx.agent import Agent
from agentx.constants import SEQUENCE, PARALLEL
from agentx.utils.helper import iter_to_aiter


class AgentXPipe:

    def __init__(
            self,
            *,
            goal: str,
            role: str,
            prompt: str,
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
            execute_type: LiteralString[SEQUENCE, PARALLEL] = SEQUENCE
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
                    *[_agent.start() async for _agent in iter_to_aiter(_agents)]
                )
            else:
                _res = await _agents.start()
            results.append(_res)
        # TODO: Needs to fix for pipe out
        # TODO: Needs to verify its goal after all set
        # TODO: Needs to retry if it fails
        return results
