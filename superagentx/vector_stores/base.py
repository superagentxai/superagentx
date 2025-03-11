from abc import ABCMeta, abstractmethod


class BaseVectorStore(metaclass=ABCMeta):

    @abstractmethod
    async def create(self, *args, **kwargs):
        """Creating a new collection or index"""
        raise NotImplementedError

    @abstractmethod
    async def insert(self, *args, **kwargs):
        """Insert Vectors into a collection"""
        raise NotImplementedError

    @abstractmethod
    async def search(self, *args, **kwargs):
        """Search for similar vectors"""
        raise NotImplementedError

    @abstractmethod
    async def update(self, *args, **kwargs):
        """Update a vector"""
        raise NotImplementedError

    @abstractmethod
    async def exists(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def delete_collection(self, *args, **kwargs):
        """Delete a collection."""
        raise NotImplementedError

    @abstractmethod
    async def delete_by_conversation_id(self, **kwargs):
        """Delete by conversation id."""
        raise NotImplementedError
