import asyncio
import uuid
from typing import List
from pydantic import BaseModel

from superagentx.db_store import StorageFactory, ConfigLoader
from superagentx.db_store.db_interface import StorageAdapter


class Agent(BaseModel):
    name: str
    agent_id: str  # Added unique ID for persistence
    human_approval_required: bool = False


class AgentManager:
    def __init__(self, storage: StorageAdapter, pipe_id: str = None):
        self.storage = storage
        # Generate a unique pipe_id if none provided (for a new run)
        self.pipe_id = pipe_id or f"pipe-{uuid.uuid4().hex[:8]}"
        self.agents: List[Agent] = [
            Agent(name="Agent Smith", agent_id="smith_01", human_approval_required=True),
            Agent(name="Auto-Bot 1", agent_id="bot_01", human_approval_required=False),
            Agent(name="Agent 007", agent_id="bond_07", human_approval_required=True),
            Agent(name="Agent Prabhu", agent_id="prabhu_01", human_approval_required=True),
        ]

    async def get_human_approval(self, agent_name: str) -> bool:
        loop = asyncio.get_running_loop()
        print(f"\n[!] Manual Review Required for: {agent_name}")
        answer = await loop.run_in_executor(
            None, lambda: input(f"    Approve {agent_name}? (y/n): ").strip().lower()
        )
        return answer == 'y'

    async def process_agents(self):
        print(f"🚀 Starting Pipe: {self.pipe_id}")

        # 1. Initialize Pipe in DB
        await self.storage.create_pipe(pipe_id=self.pipe_id, executed_by="Gemini_System")
        await self.storage.update_pipe_status(self.pipe_id, "In-Progress")

        try:
            for agent in self.agents:
                # 2. Check if this specific agent was already done in THIS pipe
                if await self.storage.is_agent_processed(self.pipe_id, agent.agent_id):
                    print(f"⏭️  Skipping {agent.name}: Already processed in this pipe.")
                    continue

                print(f"\n--- Processing {agent.name} ---")

                if agent.human_approval_required:
                    # Update Pipe status to reflect waiting
                    await self.storage.update_pipe_status(self.pipe_id, "Waiting-for-Approval")
                    is_approved = await self.get_human_approval(agent.name)

                    if not is_approved:
                        print(f"{agent.name} Rejected.")
                        await self.storage.mark_agent_completed(self.pipe_id, agent.agent_id, "REJECTED")
                        await self.storage.update_pipe_status(self.pipe_id, "Failed", error="Human rejected execution")
                        return  # Halt the entire pipe

                    await self.storage.update_pipe_status(self.pipe_id, "In-Progress")

                else:
                    print(f"⏩ Auto-approving {agent.name}...")

                # 3. Mark Agent as Completed
                await self.storage.mark_agent_completed(self.pipe_id, agent.agent_id, "COMPLETED")
                print(f"✅ {agent.name} saved to DB under Pipe {self.pipe_id}")

            # 4. Mark Pipe as Completed
            await self.storage.update_pipe_status(self.pipe_id, "Completed")
            print(f"\n🏆 Pipe {self.pipe_id} finished successfully.")

        except Exception as e:
            print(f"💥 Pipe Failed: {e}")
            await self.storage.update_pipe_status(self.pipe_id, "Failed", error=str(e))


async def main():
    try:
        # Load DB via YAML config
        storage = ConfigLoader.load_db_config("config.yaml")
        await storage.setup()

        # To Resume: Pass the pipe_id of the interrupted run here
        # To Start New: Leave it as None
        RESUME_PIPE_ID = "pipe-7b98c44c"

        manager = AgentManager(storage, pipe_id=RESUME_PIPE_ID)
        await manager.process_agents()

    except FileNotFoundError:
        print(" Error: config.yaml not found.")
    except Exception as e:
        print(f"Execution failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
