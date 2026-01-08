import asyncio
from pydantic import BaseModel
from typing import List


# 1. Define the Agent schema using Pydantic
class Agent(BaseModel):
    name: str
    human_approval_required: bool = False  # Default to False


class AgentManager:
    def __init__(self):
        # Initializing with Pydantic objects
        self.agents: List[Agent] = [
            Agent(name="Agent Smith", human_approval_required=True),
            Agent(name="Auto-Bot 1", human_approval_required=False),
            Agent(name="Agent 007", human_approval_required=True),
        ]

    async def iter_to_aiter(self, iterable):
        for item in iterable:
            yield item

    async def get_human_approval(self, agent_name: str) -> bool:
        loop = asyncio.get_event_loop()
        print(f"\n[!] Manual Review Required for: {agent_name}")

        # run_in_executor prevents input() from freezing the whole program
        answer = await loop.run_in_executor(
            None,
            lambda: input(f"    Approve {agent_name}? (y/n): ").lower()
        )
        return answer == 'y'

    async def process_agents(self):
        async for agent in self.iter_to_aiter(self.agents):
            print(f"\n--- Processing {agent.name} ---")

            # Use the Pydantic attribute
            if agent.human_approval_required:
                is_approved = await self.get_human_approval(agent.name)
            else:
                print(f"⏩ Auto-approving {agent.name}...")
                is_approved = True

            status = "ACTIVE" if is_approved else "REJECTED"
            print(f"Result: {agent.name} is {status}")


async def main():
    manager = AgentManager()
    await manager.process_agents()


if __name__ == "__main__":
    asyncio.run(main())