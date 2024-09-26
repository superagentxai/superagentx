import asyncio
from typing import LiteralString

from agentx.agent.engine import Engine
from agentx.constants import SEQUENCE, PARALLEL
from agentx.utils.helper import iter_to_aiter


class Agent:

    def __init__(
            self,
            *,
            name: str | None = None,
            description: str | None = None,
            role: str | None = None,
            goal: str | None = None,
            max_retry: int = 5
    ):
        self.engines: list[Engine | list[Engine]] = []
        self.name = name
        self.description = description
        self.role = role
        self.goal = goal
        self.max_retry = max_retry

    async def add(
            self,
            *engines: Engine,
            execute_type: LiteralString[SEQUENCE, PARALLEL] = SEQUENCE
    ):
        if execute_type == SEQUENCE:
            self.engines += engines
        else:
            self.engines.append(list(engines))

    async def _verify_goal(self):
        pass

    async def execute(self):
        results = []
        async for _engines in iter_to_aiter(self.engines):
            if isinstance(_engines, list):
                _res = await asyncio.gather(
                    *[_engine.start() async for _engine in iter_to_aiter(_engines)]
                )
            else:
                _res = await _engines.start()
            results.append(_res)
        # TODO: Needs to fix for agent out
        # TODO: Needs to verify its goal after all set
        # TODO: Needs to retry if it fails
        return results
