from typing import LiteralString

from agentx.agent.engine import Engine

SEQUENCE = 'SEQUENCE'
PARALLEL = 'PARALLEL'


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

    async def execute(self):
        pass

    async def add(
            self,
            execute_type: LiteralString[SEQUENCE, PARALLEL] = SEQUENCE,
            *engines: Engine
    ):
        if execute_type == SEQUENCE:
            self.engines += engines
        else:
            self.engines.append(list(engines))
