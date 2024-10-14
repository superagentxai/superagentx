from abc import ABC, abstractmethod


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
