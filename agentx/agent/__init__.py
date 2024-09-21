from typing import LiteralString

from agentx.agent.engine import Engine

SEQUENCE = 'SEQUENCE'
PARALLEL = 'PARALLEL'


class Agent:

    def __init__(
            self,
            *,
            engines: list[Engine],
            invoke_type: LiteralString[SEQUENCE, PARALLEL] = SEQUENCE,
            name: str | None = None,
            description: str | None = None,
            role: str | None = None,
            goal: str | None = None,
            max_retry: int | None = 5
    ):
        self.engines = engines
        self.invoke_type = invoke_type
        self.name = name
        self.description = description
        self.role = role
        self.goal = goal
        self.max_retry = max_retry

    async def start(self):
        pass

    async def sequence(
            self,
            *engines: tuple[Engine]
    ):
        pass

    async def parallel(
            self,
            *engines: tuple[Engine]
    ):
        pass
