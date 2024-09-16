from abc import ABCMeta, abstractmethod


class BaseVectorStore(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def create_collection(self, *args, **kwargs):
        """Creating a new collection"""
        raise NotImplementedError

    @abstractmethod
    def insert(self, *args, **kwargs):
        """Insert Vectors into a collection"""
        raise NotImplementedError

    @abstractmethod
    def search(self, *args, **kwargs):
        """Search for similar vectors"""
        raise NotImplementedError

    @abstractmethod
    def update(self, *args, **kwargs):
        """Update a vector"""
        raise NotImplementedError

    @abstractmethod
    def exists(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def delete_collection(self, *args, **kwargs):
        """Delete a collection."""
        raise NotImplementedError

    @abstractmethod
    async def acreate_collection(self, *args, **kwargs):
        """Creating a new collection"""
        raise NotImplementedError

    @abstractmethod
    async def ainsert(self, *args, **kwargs):
        """Insert Vectors into a collection"""
        raise NotImplementedError

    @abstractmethod
    async def asearch(self, *args, **kwargs):
        """Search for similar vectors"""
        raise NotImplementedError

    @abstractmethod
    async def aupdate(self, *args, **kwargs):
        """Update a vector"""
        raise NotImplementedError

    @abstractmethod
    async def aexists(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    async def adelete_collection(self, *args, **kwargs):
        """Delete a collection."""
        raise NotImplementedError
