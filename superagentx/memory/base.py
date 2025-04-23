from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    id: str = Field(..., description="The unique identifier for the text data")
    memory: str = Field(
        ..., description="The memory deduced from the text data"
    )
    reason: str = Field(
        ..., description="The memory deduced from the text data"
    )
    role: str = Field(
        ..., description="The memory of role"
    )
    # The metadata value can be anything and not just string. Fix it
    metadata: Dict[str, Any] | None = Field(None, description="Additional metadata for the text data")
    score: float | None = Field(None, description="The score associated with the text data")
    created_at: Any | None = Field(None, description="The timestamp when the memory was created")
    updated_at: Any | None = Field(None, description="The timestamp when the memory was updated")


class MemoryBase(ABC):

    @abstractmethod
    async def add(self, *args, **kwargs):
        """
        Add the data.
        """
        raise NotImplementedError

    @abstractmethod
    async def get(self, memory_id):
        """
        Retrieve a memory by ID.

        Args:
            memory_id (str): ID of the memory to retrieve.

        Returns:
            dict: Retrieved memory.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, memory_id, data):
        """
        Update a memory by ID.

        Args:
            memory_id (str): ID of the memory to update.
            data (dict): Data to update the memory with.

        Returns:
            dict: Updated memory.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete(self, memory_id):
        """
        Delete a memory by ID.

        Args:
            memory_id (str): ID of the memory to delete.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_by_conversation_id(self, conversation_id: str):
        """
        Delete a conversation by ID.

        Args:
            conversation_id (str): ID of the memory to delete.
        """
        raise NotImplementedError
