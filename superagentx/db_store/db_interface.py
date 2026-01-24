from abc import ABC, abstractmethod
from typing import Any


class StorageAdapter(ABC):

    @abstractmethod
    async def setup(self):
        """Initialize connection and create tables/collections."""
        pass

    @abstractmethod
    async def create_pipe(self, pipe_id: str, executed_by: str = "System"):
        pass

    @abstractmethod
    async def update_pipe_status(self, pipe_id: str, status: str, error: str = None):
        pass

    @abstractmethod
    # --- Agent Operations ---
    async def is_agent_processed(self, pipe_id: str, agent_id: str, agent_name: str) -> bool:
        pass

    @abstractmethod
    async def mark_agent_completed(self, pipe_id: str, agent_id: str, agent_name: str, status: str,
                                   input_content: str, goal_result: Any = None, updated_by: str = "System"):
        pass

    @abstractmethod
    async def close(self) -> None:
        pass