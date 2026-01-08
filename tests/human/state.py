import asyncio
import json
import os
from pydantic import BaseModel
from typing import List, Set


# 1. Define the Agent schema
class Agent(BaseModel):
    name: str
    human_approval_required: bool = False


class AgentManager:
    def __init__(self, state_file: str = "state.json"):
        self.state_file = state_file
        # Initializing with Pydantic objects
        self.agents: List[Agent] = [
            Agent(name="Agent Smith", human_approval_required=True),
            Agent(name="Auto-Bot 1", human_approval_required=False),
            Agent(name="Agent 007", human_approval_required=True),
        ]
        # Load already processed agents from the file
        self.processed_names: Set[str] = self._load_state()

    def _load_state(self) -> Set[str]:
        """Loads the list of finished agents from a local file."""
        if os.path.exists(self.state_file):
            with open(self.state_file, "r") as f:
                try:
                    return set(json.load(f))
                except json.JSONDecodeError:
                    return set()
        return set()

    def _save_state(self, agent_name: str):
        """Adds an agent name to the local file permanently."""
        self.processed_names.add(agent_name)
        with open(self.state_file, "w") as f:
            json.dump(list(self.processed_names), f)

    async def iter_to_aiter(self, iterable):
        for item in iterable:
            yield item

    async def get_human_approval(self, agent_name: str) -> bool:
        loop = asyncio.get_running_loop()
        print(f"\n[!] Manual Review Required for: {agent_name}")

        def _ask():
            return input(f"    Approve {agent_name}? (y/n): ").strip().lower()

        answer = await loop.run_in_executor(None, _ask)
        return answer == 'y'

    async def process_agents(self):
        async for agent in self.iter_to_aiter(self.agents):
            # RESUME LOGIC: Skip if already processed
            if agent.name in self.processed_names:
                print(f"⏭️  Skipping {agent.name} (Already processed in previous run)")
                continue

            print(f"\n--- Processing {agent.name} ---")

            if agent.human_approval_required:
                is_approved = await self.get_human_approval(agent.name)
            else:
                print(f"⏩ Auto-approving {agent.name}...")
                is_approved = True

            status = "ACTIVE" if is_approved else "REJECTED"
            print(f"Result: {agent.name} is {status}")

            # SAVE STATE: Mark as done so we don't repeat this on next run
            self._save_state(agent.name)


async def main():
    manager = AgentManager()
    await manager.process_agents()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nStopped by user. You can run the script again to resume where you left off.")