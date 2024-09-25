from typing import LiteralString

from agentx.agent import Agent
from agentx.constants import SEQUENCE, PARALLEL


class AgentXPipe:

    def __init__(
            self,
            *,
            name: str | None = None,
            description: str | None = None
    ):
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
        pass
