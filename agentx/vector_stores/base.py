from abc import ABCMeta, abstractmethod


class BaseVectorStore(metaclass=ABCMeta):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def create(self, *args, **kwargs):
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
    def delete(self, *args, **kwargs):
        """Delete a vector"""
        raise NotImplementedError

    @abstractmethod
    def update(self, *args, **kwargs):
        """Update a vector"""
        raise NotImplementedError

    @abstractmethod
    def exists(self, *args, ** kwargs):
        raise NotImplementedError
